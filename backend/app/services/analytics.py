"""
SprintWise - Analytics Engine
Computes completion rate, consistency index, subject scores, and trend analysis.
"""
import json
import statistics
from datetime import datetime, date, timedelta
from app import db
from app.models import Sprint, Task, TimeLog, AnalyticsCache


class AnalyticsEngine:

    @staticmethod
    def compute_sprint_metrics(sprint_id: int, user_id: int, force_refresh=False) -> dict:
        """
        Main entry point: compute all metrics for a sprint.
        Uses cache unless force_refresh=True or cache is stale.
        """
        sprint = Sprint.query.filter_by(sprint_id=sprint_id, user_id=user_id).first()
        if not sprint:
            return {}

        cache = AnalyticsCache.query.filter_by(sprint_id=sprint_id).first()
        if cache and not force_refresh and not cache.is_stale():
            return cache.to_dict()

        # Compute fresh metrics
        completion_rate = AnalyticsEngine.compute_completion_rate(sprint_id)
        consistency_index = AnalyticsEngine.compute_consistency_index(sprint_id, user_id, sprint)
        subject_scores = AnalyticsEngine.compute_subject_scores(sprint_id, user_id, sprint)
        total_study_hours = AnalyticsEngine.compute_total_study_hours(sprint_id, user_id, sprint)
        trend_slope = AnalyticsEngine.compute_trend_slope(user_id)

        # Upsert cache
        if not cache:
            cache = AnalyticsCache(sprint_id=sprint_id)
            db.session.add(cache)

        cache.completion_rate = completion_rate
        cache.consistency_index = consistency_index
        cache.subject_scores = json.dumps(subject_scores)
        cache.total_study_hours = total_study_hours
        cache.trend_slope = trend_slope
        cache.computed_at = datetime.utcnow()
        db.session.commit()

        return cache.to_dict()

    @staticmethod
    def compute_completion_rate(sprint_id: int):
        """
        Returns float 0-100 or None if no tasks exist.
        """
        tasks = Task.query.filter_by(sprint_id=sprint_id).all()
        if not tasks:
            return None
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "completed")
        return round((completed / total) * 100, 2)

    @staticmethod
    def compute_consistency_index(sprint_id: int, user_id: int, sprint: Sprint) -> float:
        """
        Ratio of unique study days to effective sprint duration.
        """
        today = date.today()
        effective_end = min(sprint.end_date, today)
        effective_start = sprint.start_date

        if effective_end < effective_start:
            return 0.0

        duration_days = (effective_end - effective_start).days + 1

        logs = TimeLog.query.filter(
            TimeLog.user_id == user_id,
            TimeLog.start_time >= datetime.combine(effective_start, datetime.min.time()),
            TimeLog.start_time <= datetime.combine(effective_end, datetime.max.time()),
            TimeLog.end_time.isnot(None)
        ).all()

        unique_study_days = len(set(log.start_time.date() for log in logs))

        # Also count days with completed tasks (in case user forgot to log time)
        completed_tasks = Task.query.filter(
            Task.sprint_id == sprint_id,
            Task.completed_at.isnot(None)
        ).all()
        for t in completed_tasks:
            if t.completed_at:
                unique_study_days = len(
                    set(list(set(log.start_time.date() for log in logs)) +
                        [t.completed_at.date() for t in completed_tasks if t.completed_at])
                )
                break

        return round(min(1.0, unique_study_days / duration_days), 4)

    @staticmethod
    def compute_subject_scores(sprint_id: int, user_id: int, sprint: Sprint) -> dict:
        """
        Per-subject blended score: completion (60%) + time investment (40%).
        """
        tasks = Task.query.filter_by(sprint_id=sprint_id).all()
        if not tasks:
            return {}

        # Group tasks by subject
        subjects = {}
        for task in tasks:
            if task.subject not in subjects:
                subjects[task.subject] = {"total": 0, "completed": 0, "estimated_mins": 0, "actual_seconds": 0}
            subjects[task.subject]["total"] += 1
            subjects[task.subject]["estimated_mins"] += task.estimated_minutes
            if task.status == "completed":
                subjects[task.subject]["completed"] += 1
            subjects[task.subject]["actual_seconds"] += task.get_total_time_spent_seconds()

        # Get user's weekly target
        from app.models import User
        user = User.query.get(user_id)
        weekly_target_hours = user.weekly_study_target_hours if user else 20.0
        subject_count = len(subjects)
        sprint_weeks = sprint.get_duration_days() / 7
        per_subject_target_hours = (weekly_target_hours / max(subject_count, 1)) * sprint_weeks

        scores = {}
        for subject, data in subjects.items():
            if data["total"] == 0:
                continue
            completion_rate = (data["completed"] / data["total"]) * 100
            actual_hours = data["actual_seconds"] / 3600
            time_score = min(1.0, actual_hours / per_subject_target_hours) * 100 if per_subject_target_hours > 0 else completion_rate
            score = round((completion_rate * 0.6) + (time_score * 0.4), 2)

            # Classification
            if score < 40:
                classification = "critical"
            elif score < 60:
                classification = "weak"
            elif score < 75:
                classification = "average"
            elif score < 90:
                classification = "strong"
            else:
                classification = "excellent"

            scores[subject] = {
                "score": score,
                "classification": classification,
                "completion_rate": round(completion_rate, 2),
                "completed": data["completed"],
                "total": data["total"],
                "actual_hours": round(actual_hours, 2),
                "target_hours": round(per_subject_target_hours, 2),
            }

        return scores

    @staticmethod
    def compute_total_study_hours(sprint_id: int, user_id: int, sprint: Sprint) -> float:
        """
        Total hours logged via time logs for this sprint.
        """
        tasks = Task.query.filter_by(sprint_id=sprint_id).all()
        task_ids = [t.task_id for t in tasks]
        if not task_ids:
            return 0.0

        logs = TimeLog.query.filter(
            TimeLog.task_id.in_(task_ids),
            TimeLog.end_time.isnot(None)
        ).all()
        total_seconds = sum(log.duration_seconds or 0 for log in logs)
        return round(total_seconds / 3600, 2)

    @staticmethod
    def compute_trend_slope(user_id: int, n_sprints: int = 4) -> float:
        """
        Linear regression slope of completion rates over last n completed sprints.
        Returns 0.0 if insufficient data.
        """
        caches = (db.session.query(AnalyticsCache, Sprint)
                  .join(Sprint, AnalyticsCache.sprint_id == Sprint.sprint_id)
                  .filter(Sprint.user_id == user_id, Sprint.status == "completed",
                          AnalyticsCache.completion_rate.isnot(None))
                  .order_by(Sprint.start_date.asc())
                  .limit(n_sprints).all())

        if len(caches) < 2:
            return 0.0

        y_values = [c[0].completion_rate for c in caches]
        x_values = list(range(len(y_values)))

        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return 0.0

        return round(numerator / denominator, 4)

    @staticmethod
    def compute_z_score_anomaly(user_id: int) -> dict:
        """
        Detect anomalous sprint performance using per-user Z-score.
        Requires at least 4 completed sprints.
        """
        caches = (db.session.query(AnalyticsCache, Sprint)
                  .join(Sprint, AnalyticsCache.sprint_id == Sprint.sprint_id)
                  .filter(Sprint.user_id == user_id, Sprint.status == "completed",
                          AnalyticsCache.completion_rate.isnot(None))
                  .order_by(Sprint.start_date.desc()).all())

        if len(caches) < 4:
            return {"is_anomalous": False, "z_score": None}

        rates = [c[0].completion_rate for c in caches]
        most_recent = rates[0]
        historical = rates[1:]

        if len(historical) < 3:
            return {"is_anomalous": False, "z_score": None}

        try:
            mean = statistics.mean(historical)
            std = statistics.stdev(historical)
            if std == 0:
                return {"is_anomalous": False, "z_score": 0.0}
            z_score = (most_recent - mean) / std
            return {
                "is_anomalous": z_score < -1.5,
                "z_score": round(z_score, 4),
                "most_recent_rate": most_recent,
                "historical_mean": round(mean, 2),
            }
        except Exception:
            return {"is_anomalous": False, "z_score": None}
