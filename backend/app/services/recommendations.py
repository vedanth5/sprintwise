"""
SprintWise - AI Recommendation Engine
12-rule evaluation system with deduplication, priority ordering, and lifecycle management.
"""
import json
from datetime import datetime, date, timedelta
from app import db
from app.models import Sprint, Task, TimeLog, Recommendation, AnalyticsCache, User
from app.services.analytics import AnalyticsEngine

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class RecommendationEngine:

    @staticmethod
    def evaluate_rules(user_id: int) -> list:
        """
        Evaluate all 12 rules for the given user.
        Create new recommendations for triggered rules (with deduplication).
        Return list of active recommendation dicts.
        """
        user = User.query.get(user_id)
        if not user:
            return []

        active_sprint = (Sprint.query.filter_by(user_id=user_id, status="active")
                         .order_by(Sprint.start_date.desc()).first())

        metrics = {}
        if active_sprint:
            metrics = AnalyticsEngine.compute_sprint_metrics(
                active_sprint.sprint_id, user_id, force_refresh=True
            )

        # Collect all generated recommendations
        generated = []

        if active_sprint:
            generated += RecommendationEngine._eval_productivity_rules(user_id, user, active_sprint, metrics)
            generated += RecommendationEngine._eval_subject_rules(user_id, user, active_sprint, metrics)
            generated += RecommendationEngine._eval_schedule_rules(user_id, user, active_sprint, metrics)
        else:
            generated += RecommendationEngine._eval_no_sprint_rule(user_id)

        generated += RecommendationEngine._eval_recovery_rule(user_id)

        # Persist new recommendations (with deduplication)
        for rec_data in generated:
            existing = Recommendation.query.filter_by(
                user_id=user_id,
                rule_id=rec_data["rule_id"],
                sprint_id=rec_data.get("sprint_id"),
                is_dismissed=False
            ).first()

            if existing:
                # Update body with fresh data
                existing.body = rec_data["body"]
                existing.generated_at = datetime.utcnow()
            else:
                rec = Recommendation(
                    user_id=user_id,
                    sprint_id=rec_data.get("sprint_id"),
                    rule_id=rec_data["rule_id"],
                    category=rec_data["category"],
                    priority=rec_data["priority"],
                    title=rec_data["title"],
                    body=rec_data["body"],
                )
                db.session.add(rec)

        db.session.commit()

        # Return top 3 active recommendations sorted by priority
        active = (Recommendation.query.filter_by(user_id=user_id, is_dismissed=False)
                  .order_by(Recommendation.generated_at.desc()).all())
        active.sort(key=lambda r: (PRIORITY_ORDER.get(r.priority, 99), -r.rec_id))
        return [r.to_dict() for r in active[:3]]

    # ──────────────────────────────────────────────────────────────
    # Productivity Rules
    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def _eval_productivity_rules(user_id, user, sprint, metrics):
        recs = []
        today = date.today()
        elapsed_days = (today - sprint.start_date).days + 1
        duration_days = sprint.get_duration_days()
        elapsed_pct = min(100, (elapsed_days / duration_days) * 100) if duration_days > 0 else 0
        completion_rate = metrics.get("completion_rate") or 0
        days_remaining = max(0, (sprint.end_date - today).days)

        tasks = Task.query.filter_by(sprint_id=sprint.sprint_id).all()
        total_tasks = len(tasks)
        tasks_remaining = sum(1 for t in tasks if t.status != "completed")

        # R-P01: Sprint at risk (< 40% complete with > 3 days elapsed)
        if elapsed_days > 3 and completion_rate < 40 and total_tasks > 0:
            suggested_extra = max(30, int((tasks_remaining * 30) / max(days_remaining, 1)))
            recs.append({
                "rule_id": "R-P01",
                "category": "productivity",
                "priority": "high",
                "sprint_id": sprint.sprint_id,
                "title": f"Sprint at Risk: Only {completion_rate:.0f}% Complete",
                "body": (
                    f"Your '{sprint.name}' sprint is {elapsed_pct:.0f}% through but only "
                    f"{completion_rate:.0f}% of tasks are done. You have {tasks_remaining} tasks "
                    f"remaining across {days_remaining} days. Consider extending daily study by "
                    f"{suggested_extra} minutes or removing low-priority tasks to stay on track."
                )
            })

        # R-P02: No activity in last 2 days
        two_days_ago = datetime.combine(today - timedelta(days=2), datetime.min.time())
        recent_logs = TimeLog.query.filter(
            TimeLog.user_id == user_id,
            TimeLog.start_time >= two_days_ago
        ).first()
        recent_completion = Task.query.filter(
            Task.sprint_id == sprint.sprint_id,
            Task.completed_at >= two_days_ago
        ).first()

        if not recent_logs and not recent_completion and elapsed_days > 2:
            last_log = (TimeLog.query.filter_by(user_id=user_id)
                        .order_by(TimeLog.start_time.desc()).first())
            last_date_str = last_log.start_time.strftime("%b %d") if last_log else "unknown"
            recs.append({
                "rule_id": "R-P02",
                "category": "productivity",
                "priority": "high",
                "sprint_id": sprint.sprint_id,
                "title": "2-Day Study Gap Detected",
                "body": (
                    f"No study activity recorded in the last 2 days. Your last logged session was on "
                    f"{last_date_str}. Even a 25-minute focused session today will protect your "
                    f"consistency score. What's one task you can complete right now?"
                )
            })

        # R-P04: Declining trend (handled in recovery rules, but check here for active sprint context)
        trend_slope = metrics.get("trend_slope") or 0
        if trend_slope < -3.0:
            recs.append({
                "rule_id": "R-P04",
                "category": "productivity",
                "priority": "high",
                "sprint_id": sprint.sprint_id,
                "title": "Performance Trend: Declining",
                "body": (
                    f"Your sprint completion rate has been declining over your last few sprints "
                    f"(trend slope: {trend_slope:.1f} points/sprint). Consider reviewing your sprint "
                    f"scope — are tasks consistently over-estimated, or is study time being displaced "
                    f"by other commitments? Try reducing sprint size by 20% next sprint."
                )
            })

        return recs

    # ──────────────────────────────────────────────────────────────
    # Subject Rules
    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def _eval_subject_rules(user_id, user, sprint, metrics):
        recs = []
        subject_scores = metrics.get("subject_scores") or {}
        today = date.today()
        elapsed_days = (today - sprint.start_date).days + 1
        duration_days = sprint.get_duration_days()
        elapsed_pct = min(100, (elapsed_days / duration_days) * 100) if duration_days > 0 else 0

        # R-S01: Any subject score < 40 with >= 3 tasks
        weak_subjects = [
            (s, d) for s, d in subject_scores.items()
            if d["score"] < 40 and d["total"] >= 3
        ]
        for subject, data in weak_subjects[:1]:  # max 1 subject alert at a time
            recommended_tasks = max(1, data["total"] - data["completed"])
            recs.append({
                "rule_id": "R-S01",
                "category": "subject",
                "priority": "high",
                "sprint_id": sprint.sprint_id,
                "title": f"Weak Subject Alert: {subject}",
                "body": (
                    f"Your '{subject}' performance score is {data['score']:.0f}/100 — the weakest "
                    f"subject in your current sprint. Only {data['completed']}/{data['total']} tasks "
                    f"are complete. Prioritize at least {recommended_tasks} '{subject}' tasks in your "
                    f"next study session. Current study time: {data['actual_hours']:.1f}h "
                    f"(target: {data['target_hours']:.1f}h)."
                )
            })

        # R-S02: Subject time investment < 30% of target with > 50% sprint elapsed
        if elapsed_pct > 50:
            for subject, data in subject_scores.items():
                if (data["target_hours"] > 0 and
                        data["actual_hours"] / data["target_hours"] < 0.3):
                    hours_needed = data["target_hours"] - data["actual_hours"]
                    recs.append({
                        "rule_id": "R-S02",
                        "category": "subject",
                        "priority": "medium",
                        "sprint_id": sprint.sprint_id,
                        "title": f"Low Time Investment: {subject}",
                        "body": (
                            f"You've invested only {data['actual_hours']:.1f}h in '{subject}' "
                            f"({data['actual_hours']/data['target_hours']*100:.0f}% of target), "
                            f"and your sprint is {elapsed_pct:.0f}% complete. You need roughly "
                            f"{hours_needed:.1f} more hours to hit your target for this subject."
                        )
                    })
                    break  # Only one R-S02 at a time

        # R-S03: Single subject > 70% of completed tasks (overemphasis)
        if subject_scores:
            total_done = sum(d["completed"] for d in subject_scores.values())
            if total_done > 5:
                for subject, data in subject_scores.items():
                    if data["completed"] / total_done > 0.70:
                        recs.append({
                            "rule_id": "R-S03",
                            "category": "subject",
                            "priority": "medium",
                            "sprint_id": sprint.sprint_id,
                            "title": f"Overemphasis on {subject}",
                            "body": (
                                f"{data['completed']}/{total_done} of your completed tasks "
                                f"({data['completed']/total_done*100:.0f}%) are in '{subject}'. "
                                f"Consider balancing time across your other subjects to avoid "
                                f"neglecting areas that may appear in assessments."
                            )
                        })
                        break

        return recs

    # ──────────────────────────────────────────────────────────────
    # Schedule Rules
    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def _eval_schedule_rules(user_id, user, sprint, metrics):
        recs = []
        today = date.today()
        consistency_index = metrics.get("consistency_index") or 0
        elapsed_days = (today - sprint.start_date).days + 1
        duration_days = sprint.get_duration_days()
        elapsed_pct = min(100, (elapsed_days / duration_days) * 100) if duration_days > 0 else 0

        # R-SC01: Consistency < 50% with sprint > 50% elapsed
        if elapsed_pct > 50 and consistency_index < 0.5:
            study_days = round(consistency_index * elapsed_days)
            recs.append({
                "rule_id": "R-SC01",
                "category": "schedule",
                "priority": "high",
                "sprint_id": sprint.sprint_id,
                "title": "Study Consistency Warning",
                "body": (
                    f"You've studied on approximately {study_days} of the last {elapsed_days} days "
                    f"({consistency_index*100:.0f}% consistency). Research consistently shows that "
                    f"distributed practice outperforms cramming for retention. Aim for at least one "
                    f"task completion per day to build momentum."
                )
            })

        # R-SC02: Cramming pattern - most tasks done in last 2 days
        tasks = Task.query.filter(
            Task.sprint_id == sprint.sprint_id,
            Task.status == "completed"
        ).all()
        if len(tasks) >= 5:
            two_days_ago = datetime.combine(today - timedelta(days=2), datetime.min.time())
            recent_completions = sum(1 for t in tasks if t.completed_at and t.completed_at >= two_days_ago)
            cramming_pct = (recent_completions / len(tasks)) * 100
            if cramming_pct > 60:
                recs.append({
                    "rule_id": "R-SC02",
                    "category": "schedule",
                    "priority": "medium",
                    "sprint_id": sprint.sprint_id,
                    "title": "Cramming Pattern Detected",
                    "body": (
                        f"{cramming_pct:.0f}% of your completed tasks were finished in the last 2 days. "
                        f"While this sprint may still succeed numerically, the retention impact is "
                        f"significantly lower than distributed study. In your next sprint, try completing "
                        f"at least 2 tasks per day from day 1."
                    )
                })

        return recs

    @staticmethod
    def _eval_no_sprint_rule(user_id):
        """R-SC03: No active sprint and last sprint ended > 3 days ago."""
        last_sprint = (Sprint.query.filter_by(user_id=user_id)
                       .order_by(Sprint.end_date.desc()).first())
        if not last_sprint:
            return [{
                "rule_id": "R-SC03",
                "category": "schedule",
                "priority": "low",
                "sprint_id": None,
                "title": "Ready to Start Your First Sprint?",
                "body": ("You haven't created a study sprint yet. Creating your first sprint takes "
                         "under 2 minutes: pick a subject, set a 7-day window, and add 3–5 tasks. "
                         "Start small and build the habit.")
            }]

        days_since = (date.today() - last_sprint.end_date).days
        if days_since > 3:
            return [{
                "rule_id": "R-SC03",
                "category": "schedule",
                "priority": "low",
                "sprint_id": None,
                "title": f"No Active Sprint ({days_since} Days Gap)",
                "body": (
                    f"Your last sprint '{last_sprint.name}' ended {days_since} days ago. "
                    f"Maintaining sprint continuity is key to consistent progress. "
                    f"Create a new sprint now to keep your momentum going."
                )
            }]
        return []

    @staticmethod
    def _eval_recovery_rule(user_id):
        """R-RC01: First good sprint after declining trend."""
        caches = (db.session.query(AnalyticsCache, Sprint)
                  .join(Sprint, AnalyticsCache.sprint_id == Sprint.sprint_id)
                  .filter(Sprint.user_id == user_id, Sprint.status == "completed")
                  .order_by(Sprint.start_date.desc()).limit(4).all())

        if len(caches) < 3:
            return []

        rates = [c[0].completion_rate for c in caches if c[0].completion_rate is not None]
        if len(rates) < 3:
            return []

        # Most recent sprint shows improvement after 2+ declining sprints
        if rates[0] > 60 and rates[1] < rates[0] - 15 and rates[2] < rates[0] - 10:
            return [{
                "rule_id": "R-RC01",
                "category": "recovery",
                "priority": "low",
                "sprint_id": caches[0][1].sprint_id,
                "title": "Great Recovery! Momentum Restored",
                "body": (
                    f"Your last sprint hit {rates[0]:.0f}% completion after a dip in your "
                    f"previous sprints. This recovery shows strong self-regulation. "
                    f"Keep the current schedule and task scope — it's working."
                )
            }]
        return []

    @staticmethod
    def compute_next_task_suggestion(sprint_id: int, user_id: int) -> dict:
        """
        Returns the highest-priority pending task using the scoring formula:
        score = (priority_weight * 0.4) + (subject_urgency * 0.35) + (time_pressure * 0.25)
        """
        sprint = Sprint.query.filter_by(sprint_id=sprint_id, user_id=user_id).first()
        if not sprint:
            return {}

        pending_tasks = Task.query.filter_by(sprint_id=sprint_id, status="pending").all()
        if not pending_tasks:
            return {}

        cache = AnalyticsCache.query.filter_by(sprint_id=sprint_id).first()
        subject_scores = {}
        if cache and cache.subject_scores:
            subject_scores = json.loads(cache.subject_scores)

        today = date.today()
        days_remaining = max(0, (sprint.end_date - today).days)
        duration_days = sprint.get_duration_days()
        days_elapsed = (today - sprint.start_date).days
        time_pressure_ratio = days_elapsed / duration_days if duration_days > 0 else 0

        def score_task(task):
            priority_weight = {"high": 1.0, "medium": 0.6, "low": 0.2}.get(task.priority, 0.6)
            subj_data = subject_scores.get(task.subject, {})
            subj_score = subj_data.get("score", 75)
            subject_urgency = 1.0 if subj_score < 50 else (0.6 if subj_score < 70 else 0.2)
            time_pressure = 1.0 if time_pressure_ratio > 0.7 else (0.5 if time_pressure_ratio > 0.4 else 0.1)
            return (priority_weight * 0.4) + (subject_urgency * 0.35) + (time_pressure * 0.25)

        best_task = max(pending_tasks, key=score_task)
        result = best_task.to_dict()
        result["suggestion_reason"] = (
            f"Prioritized due to: subject score {subject_scores.get(best_task.subject, {}).get('score', 'N/A')}, "
            f"priority: {best_task.priority}, sprint {int(time_pressure_ratio*100)}% elapsed."
        )
        return result
