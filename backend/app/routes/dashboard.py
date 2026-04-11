"""
SprintWise - Dashboard Routes
Single aggregation endpoint that powers the student dashboard.
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from app import db
from app.models import Sprint, Task, TimeLog, AnalyticsCache
from app.services.analytics import AnalyticsEngine
from app.services.recommendations import RecommendationEngine

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/summary")
@jwt_required()
def get_summary():
    user_id = int(get_jwt_identity())

    # ── Active Sprint ──
    active_sprint = (Sprint.query.filter_by(user_id=user_id, status="active")
                     .order_by(Sprint.start_date.desc()).first())

    active_sprint_data = None
    metrics = {}
    next_task_suggestion = None

    if active_sprint:
        metrics = AnalyticsEngine.compute_sprint_metrics(active_sprint.sprint_id, user_id)
        active_sprint_data = active_sprint.to_dict(include_tasks=True)
        active_sprint_data["metrics"] = metrics

        # Next task suggestion
        next_task_suggestion = RecommendationEngine.compute_next_task_suggestion(
            active_sprint.sprint_id, user_id
        )

    # ── Sprint Trend (last 4 completed sprints for chart) ──
    trend_sprints = (db.session.query(Sprint, AnalyticsCache)
                     .outerjoin(AnalyticsCache, Sprint.sprint_id == AnalyticsCache.sprint_id)
                     .filter(Sprint.user_id == user_id)
                     .order_by(Sprint.start_date.desc()).limit(5).all())

    sprint_trend = []
    for sprint, cache in trend_sprints:
        sprint_trend.append({
            "sprint_id": sprint.sprint_id,
            "name": sprint.name,
            "start_date": sprint.start_date.isoformat(),
            "status": sprint.status,
            "completion_rate": cache.completion_rate if cache else None,
            "consistency_index": cache.consistency_index if cache else None,
        })

    # ── Weekly Study Hours ──
    week_start = datetime.combine(date.today() - timedelta(days=6), datetime.min.time())
    week_logs = TimeLog.query.filter(
        TimeLog.user_id == user_id,
        TimeLog.start_time >= week_start,
        TimeLog.end_time.isnot(None)
    ).all()
    weekly_hours = round(sum(l.duration_seconds or 0 for l in week_logs) / 3600, 2)

    # ── Study Streak (consecutive days with at least 1 completed task) ──
    streak = 0
    check_date = date.today()
    while True:
        day_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.status == "completed",
            db.func.date(Task.completed_at) == check_date
        ).first()
        if day_tasks:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
        if streak > 365:
            break

    # ── Recommendations ──
    recommendations = RecommendationEngine.evaluate_rules(user_id)

    # ── Total stats ──
    total_sprints = Sprint.query.filter_by(user_id=user_id).count()
    total_tasks_done = Task.query.filter_by(user_id=user_id, status="completed").count()

    return jsonify({
        "active_sprint": active_sprint_data,
        "sprint_trend": sprint_trend,
        "subject_scores": metrics.get("subject_scores", {}),
        "consistency_index": metrics.get("consistency_index"),
        "total_study_hours_week": weekly_hours,
        "study_streak_days": streak,
        "recommendations": recommendations,
        "next_task_suggestion": next_task_suggestion,
        "stats": {
            "total_sprints": total_sprints,
            "total_tasks_completed": total_tasks_done,
        }
    }), 200
