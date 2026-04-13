"""
SprintWise - Authentication Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from datetime import datetime, timedelta
from app import db
from app.models import User
from app.services.mail_service import MailService

auth_bp = Blueprint("auth", __name__)


def _validate_registration(data):
    errors = {}
    if not data.get("email") or "@" not in data["email"]:
        errors["email"] = "Valid email required"
    if not data.get("password") or len(data["password"]) < 8:
        errors["password"] = "Password must be at least 8 characters"
    if not data.get("full_name") or len(data["full_name"].strip()) < 2:
        errors["full_name"] = "Full name required"
    return errors


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    errors = _validate_registration(data)
    if errors:
        return jsonify({"errors": errors}), 400

    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "Email already registered"}), 409

    try:
        user = User(
            email=data["email"].lower().strip(),
            full_name=data["full_name"].strip(),
            academic_level=data.get("academic_level", "undergraduate"),
            weekly_study_target_hours=float(data.get("weekly_study_target_hours", 20.0)),
        )
        user.set_password(data["password"])
        
        # Generate and "send" OTP
        otp = MailService.generate_otp()
        user.otp_code = otp
        user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        
        db.session.add(user)
        db.session.commit()

        MailService.send_otp(user.email, otp)
    except Exception as e:
        print(f"❌ REGISTRATION ERROR: {str(e)}")
        return jsonify({"error": "Internal server error during registration", "details": str(e)}), 500

    return jsonify({
        "message": "Account created. Please verify your email.",
        "email": user.email,
        "is_verified": False
    }), 201


@auth_bp.post("/verify-otp")
def verify_otp():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").lower().strip()
    code = data.get("code", "").strip()

    if not email or not code:
        return jsonify({"error": "Email and code required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.is_verified:
        return jsonify({"message": "Email already verified"}), 200

    if user.otp_code != code:
        return jsonify({"error": "Invalid verification code"}), 400

    if user.otp_expiry < datetime.utcnow():
        return jsonify({"error": "Code expired. Please request a new one."}), 400

    user.is_verified = True
    user.otp_code = None
    user.otp_expiry = None
    db.session.commit()

    access_token = create_access_token(identity=str(user.user_id))
    refresh_token = create_refresh_token(identity=str(user.user_id))

    return jsonify({
        "message": "Email verified successfully",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }), 200


@auth_bp.post("/resend-otp")
def resend_otp():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").lower().strip()

    if not email:
        return jsonify({"error": "Email required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    otp = MailService.generate_otp()
    user.otp_code = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()

    MailService.send_otp(user.email, otp)
    return jsonify({"message": "New verification code sent"}), 200


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.is_verified:
        return jsonify({
            "error": "Account not verified",
            "needs_verification": True,
            "email": user.email
        }), 403

    user.last_login = datetime.utcnow()
    db.session.commit()

    access_token = create_access_token(identity=str(user.user_id))
    refresh_token = create_refresh_token(identity=str(user.user_id))

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }), 200


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": access_token}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.put("/profile")
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    import json
    if "full_name" in data:
        user.full_name = data["full_name"].strip()
    if "academic_level" in data:
        user.academic_level = data["academic_level"]
    if "weekly_study_target_hours" in data:
        try:
            user.weekly_study_target_hours = float(data["weekly_study_target_hours"])
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid weekly_study_target_hours"}), 400
    if "subjects" in data and isinstance(data["subjects"], list):
        user.subjects = json.dumps(data["subjects"])

    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200
