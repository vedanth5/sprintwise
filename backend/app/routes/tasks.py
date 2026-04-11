"""
SprintWise - Task Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Sprint, Task

task_bp = Blueprint("tasks", __name__)

VALID_STATUSES = {"pending", "in_progress", "completed"}
VALID_PRIORITIES = {"low", "medium", "high"}


def _validate_task(data):
    errors = {}
    if not data.get("sprint_id"):
        errors["sprint_id"] = "sprint_id required"
    if not data.get("subject") or len(data["subject"].strip()) < 1:
        errors["subject"] = "Subject required"
    if not data.get("description") or len(data["description"].strip()) < 2:
        errors["description"] = "Description required (min 2 chars)"
    try:
        mins = int(data.get("estimated_minutes", 30))
        if not (1 <= mins <= 480):
            errors["estimated_minutes"] = "estimated_minutes must be 1–480"
    except (ValueError, TypeError):
        errors["estimated_minutes"] = "Must be an integer"
    return errors


@task_bp.post("/")
@jwt_required()
def create_task():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    errors = _validate_task(data)
    if errors:
        return jsonify({"errors": errors}), 400

    sprint = Sprint.query.filter_by(sprint_id=data["sprint_id"], user_id=user_id).first()
    if not sprint:
        return jsonify({"error": "Sprint not found or access denied"}), 404

    task = Task(
        sprint_id=sprint.sprint_id,
        user_id=user_id,
        subject=data["subject"].strip(),
        description=data["description"].strip(),
        estimated_minutes=int(data.get("estimated_minutes", 30)),
        priority=data.get("priority", "medium") if data.get("priority") in VALID_PRIORITIES else "medium",
        status="pending",
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({"message": "Task created", "task": task.to_dict()}), 201


@task_bp.post("/bulk")
@jwt_required()
def create_tasks_bulk():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    tasks_data = data.get("tasks", [])

    if not isinstance(tasks_data, list) or len(tasks_data) == 0:
        return jsonify({"error": "tasks array required"}), 400
    if len(tasks_data) > 50:
        return jsonify({"error": "Maximum 50 tasks per bulk request"}), 400

    sprint_id = data.get("sprint_id")
    sprint = Sprint.query.filter_by(sprint_id=sprint_id, user_id=user_id).first()
    if not sprint:
        return jsonify({"error": "Sprint not found or access denied"}), 404

    created = []
    for td in tasks_data:
        task = Task(
            sprint_id=sprint_id,
            user_id=user_id,
            subject=str(td.get("subject", "General")).strip(),
            description=str(td.get("description", "")).strip(),
            estimated_minutes=int(td.get("estimated_minutes", 30)),
            priority=td.get("priority", "medium") if td.get("priority") in VALID_PRIORITIES else "medium",
            status="pending",
        )
        db.session.add(task)
        created.append(task)

    db.session.commit()
    return jsonify({"message": f"{len(created)} tasks created", "tasks": [t.to_dict() for t in created]}), 201


@task_bp.get("/sprint/<int:sprint_id>")
@jwt_required()
def get_sprint_tasks(sprint_id):
    user_id = int(get_jwt_identity())
    sprint = Sprint.query.filter_by(sprint_id=sprint_id, user_id=user_id).first()
    if not sprint:
        return jsonify({"error": "Sprint not found or access denied"}), 404

    status_filter = request.args.get("status")
    query = Task.query.filter_by(sprint_id=sprint_id, user_id=user_id)
    if status_filter and status_filter in VALID_STATUSES:
        query = query.filter_by(status=status_filter)
    tasks = query.order_by(Task.created_at.asc()).all()
    return jsonify({"tasks": [t.to_dict() for t in tasks], "total": len(tasks)}), 200


@task_bp.patch("/<int:task_id>")
@jwt_required()
def update_task(task_id):
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Task not found or access denied"}), 404

    data = request.get_json(silent=True) or {}

    if "status" in data:
        new_status = data["status"]
        if new_status not in VALID_STATUSES:
            return jsonify({"error": f"Invalid status. Must be one of: {VALID_STATUSES}"}), 400
        task.status = new_status
        if new_status == "completed" and not task.completed_at:
            task.completed_at = datetime.utcnow()
        elif new_status != "completed":
            task.completed_at = None

    if "description" in data:
        task.description = data["description"].strip()
    if "subject" in data:
        task.subject = data["subject"].strip()
    if "estimated_minutes" in data:
        try:
            task.estimated_minutes = int(data["estimated_minutes"])
        except (ValueError, TypeError):
            return jsonify({"error": "estimated_minutes must be integer"}), 400
    if "priority" in data and data["priority"] in VALID_PRIORITIES:
        task.priority = data["priority"]

    db.session.commit()
    return jsonify({"message": "Task updated", "task": task.to_dict()}), 200


@task_bp.delete("/<int:task_id>")
@jwt_required()
def delete_task(task_id):
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Task not found or access denied"}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"}), 200
