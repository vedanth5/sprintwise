"""
SprintWise - Time Tracking Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Task, TimeLog

timelog_bp = Blueprint("timelogs", __name__)


@timelog_bp.post("/start")
@jwt_required()
def start_session():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    task_id = data.get("task_id")

    if not task_id:
        return jsonify({"error": "task_id required"}), 400

    task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Task not found or access denied"}), 404

    # Prevent duplicate open sessions for this task
    open_log = TimeLog.query.filter_by(task_id=task_id, user_id=user_id, end_time=None).first()
    if open_log:
        return jsonify({"message": "Session already active", "log": open_log.to_dict()}), 200

    log = TimeLog(task_id=task_id, user_id=user_id)
    db.session.add(log)

    # Auto-transition task to in_progress
    if task.status == "pending":
        task.status = "in_progress"

    db.session.commit()
    return jsonify({"message": "Session started", "log": log.to_dict()}), 201


@timelog_bp.post("/stop")
@jwt_required()
def stop_session():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    log_id = data.get("log_id")
    task_id = data.get("task_id")

    if log_id:
        log = TimeLog.query.filter_by(log_id=log_id, user_id=user_id, end_time=None).first()
    elif task_id:
        log = TimeLog.query.filter_by(task_id=task_id, user_id=user_id, end_time=None).first()
    else:
        return jsonify({"error": "log_id or task_id required"}), 400

    if not log:
        return jsonify({"error": "No active session found"}), 404

    log.stop_session()
    db.session.commit()
    return jsonify({"message": "Session stopped", "log": log.to_dict()}), 200


@timelog_bp.get("/task/<int:task_id>")
@jwt_required()
def get_task_logs(task_id):
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"error": "Task not found or access denied"}), 404

    logs = TimeLog.query.filter_by(task_id=task_id).order_by(TimeLog.start_time.desc()).all()
    total_seconds = sum(l.duration_seconds or 0 for l in logs if l.end_time)
    return jsonify({
        "logs": [l.to_dict() for l in logs],
        "total_sessions": len(logs),
        "total_seconds": total_seconds,
        "total_hours": round(total_seconds / 3600, 2),
    }), 200


@timelog_bp.get("/active")
@jwt_required()
def get_active_sessions():
    user_id = int(get_jwt_identity())
    active = TimeLog.query.filter_by(user_id=user_id, end_time=None).all()
    return jsonify({"active_sessions": [l.to_dict() for l in active]}), 200
