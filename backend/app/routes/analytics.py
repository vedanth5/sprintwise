"""
SprintWise - Analytics Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Sprint
from app.services.analytics import AnalyticsEngine

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/sprint/<int:sprint_id>")
@jwt_required()
def get_sprint_analytics(sprint_id):
    user_id = int(get_jwt_identity())
    sprint = Sprint.query.filter_by(sprint_id=sprint_id, user_id=user_id).first()
    if not sprint:
        return jsonify({"error": "Sprint not found"}), 404

    force = request.args.get("refresh", "false").lower() == "true"
    metrics = AnalyticsEngine.compute_sprint_metrics(sprint_id, user_id, force_refresh=force)
    return jsonify({"sprint_id": sprint_id, "metrics": metrics}), 200


@analytics_bp.get("/history")
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    from app import db
    from app.models import AnalyticsCache
    results = (db.session.query(AnalyticsCache, Sprint)
               .join(Sprint, AnalyticsCache.sprint_id == Sprint.sprint_id)
               .filter(Sprint.user_id == user_id)
               .order_by(Sprint.start_date.desc()).limit(10).all())

    history = []
    for cache, sprint in results:
        entry = cache.to_dict()
        entry["sprint_name"] = sprint.name
        entry["sprint_id"] = sprint.sprint_id
        entry["start_date"] = sprint.start_date.isoformat()
        entry["end_date"] = sprint.end_date.isoformat()
        entry["status"] = sprint.status
        history.append(entry)

    return jsonify({"history": history}), 200


@analytics_bp.get("/anomaly")
@jwt_required()
def get_anomaly():
    user_id = int(get_jwt_identity())
    result = AnalyticsEngine.compute_z_score_anomaly(user_id)
    return jsonify(result), 200
