"""
SprintWise - Sprint Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from app import db
from app.models import Sprint
from app.services.analytics import AnalyticsEngine

sprint_bp = Blueprint("sprints", __name__)


def _validate_sprint(data, user_id, sprint_id=None):
    errors = {}
    if not data.get("name") or len(data["name"].strip()) < 2:
        errors["name"] = "Sprint name required (min 2 chars)"
    try:
        start = date.fromisoformat(data["start_date"])
        end = date.fromisoformat(data["end_date"])
        if end <= start:
            errors["end_date"] = "end_date must be after start_date"
        if (end - start).days > 30:
            errors["end_date"] = "Sprint duration cannot exceed 30 days"
    except (KeyError, ValueError):
        errors["dates"] = "Valid start_date and end_date (YYYY-MM-DD) required"
    return errors


@sprint_bp.get("/")
@jwt_required()
def list_sprints():
    user_id = int(get_jwt_identity())
    status_filter = request.args.get("status", "all")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    query = Sprint.query.filter_by(user_id=user_id)
    if status_filter != "all":
        query = query.filter_by(status=status_filter)

    query = query.order_by(Sprint.start_date.desc())
    total = query.count()
    sprints = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "sprints": [s.to_dict() for s in sprints],
        "total": total,
        "page": page,
        "per_page": per_page,
    }), 200


@sprint_bp.post("/")
@jwt_required()
def create_sprint():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    errors = _validate_sprint(data, user_id)
    if errors:
        return jsonify({"errors": errors}), 400

    sprint = Sprint(
        user_id=user_id,
        name=data["name"].strip(),
        start_date=date.fromisoformat(data["start_date"]),
        end_date=date.fromisoformat(data["end_date"]),
        notes=data.get("notes", ""),
        status="active",
    )
    db.session.add(sprint)
    db.session.commit()
    return jsonify({"message": "Sprint created", "sprint": sprint.to_dict()}), 201


@sprint_bp.get("/<int:sprint_id>")
@jwt_required()
def get_sprint(sprint_id):
    user_id = int(get_jwt_identity())
    sprint = Sprint.query.filter_by(sprint_id=sprint_id, user_id=user_id).first()
    if not sprint:
        return jsonify({"error": "Sprint not found"}), 404
    return jsonify({"sprint": sprint.to_dict(include_tasks=True)}), 200


@sprint_bp.put("/<int:sprint_id>")
@jwt_required()
def update_sprint(sprint_id):
    user_id = int(get_jwt_identity())
    sprint = Sprint.query.filter_by(sprint_id=sprint_id, user_id=user_id).first()
    if not sprint:
        return jsonify({"error": "Sprint not found"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data:
        sprint.name = data["name"].strip()
    if "notes" in data:
        sprint.notes = data["notes"]
    if "start_date" in data:
        try:
            sprint.start_date = date.fromisoformat(data["start_date"])
        except ValueError:
            return jsonify({"error": "Invalid start_date"}), 400
    if "end_date" in data:
        try:
            sprint.end_date = date.fromisoformat(data["end_date"])
        except ValueError:
            return jsonify({"error": "Invalid end_date"}), 400

    db.session.commit()
    return jsonify({"message": "Sprint updated", "sprint": sprint.to_dict()}), 200


@sprint_bp.patch("/<int:sprint_id>/complete")
@jwt_required()
def complete_sprint(sprint_id):
    user_id = int(get_jwt_identity())
    sprint = Sprint.query.filter_by(sprint_id=sprint_id, user_id=user_id).first()
    if not sprint:
        return jsonify({"error": "Sprint not found"}), 404
    if sprint.status == "completed":
        return jsonify({"message": "Sprint already completed"}), 200

    sprint.status = "completed"
    db.session.commit()

    # Compute final analytics and cache
    metrics = AnalyticsEngine.compute_sprint_metrics(sprint_id, user_id, force_refresh=True)
    return jsonify({"message": "Sprint completed", "sprint": sprint.to_dict(), "final_metrics": metrics}), 200


@sprint_bp.delete("/<int:sprint_id>")
@jwt_required()
def delete_sprint(sprint_id):
    user_id = int(get_jwt_identity())
    sprint = Sprint.query.filter_by(sprint_id=sprint_id, user_id=user_id).first()
    if not sprint:
        return jsonify({"error": "Sprint not found"}), 404
    db.session.delete(sprint)
    db.session.commit()
    return jsonify({"message": "Sprint deleted"}), 200
