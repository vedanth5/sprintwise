"""
SprintWise - Recommendations Routes
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Recommendation
from app.services.recommendations import RecommendationEngine

rec_bp = Blueprint("recommendations", __name__)


@rec_bp.get("/")
@jwt_required()
def get_recommendations():
    user_id = int(get_jwt_identity())
    recs = RecommendationEngine.evaluate_rules(user_id)
    return jsonify({"recommendations": recs, "count": len(recs)}), 200


@rec_bp.patch("/<int:rec_id>/dismiss")
@jwt_required()
def dismiss_recommendation(rec_id):
    user_id = int(get_jwt_identity())
    rec = Recommendation.query.filter_by(rec_id=rec_id, user_id=user_id).first()
    if not rec:
        return jsonify({"error": "Recommendation not found"}), 404
    rec.dismiss()
    db.session.commit()
    return jsonify({"message": "Recommendation dismissed"}), 200


@rec_bp.get("/all")
@jwt_required()
def get_all_recommendations():
    user_id = int(get_jwt_identity())
    recs = (Recommendation.query.filter_by(user_id=user_id)
            .order_by(Recommendation.generated_at.desc()).limit(20).all())
    return jsonify({"recommendations": [r.to_dict() for r in recs]}), 200
