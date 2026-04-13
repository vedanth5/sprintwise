"""
SprintWise Backend - Flask Application Factory
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy import text
import os

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app(config=None):
    app = Flask(__name__)

    # --- Configuration ---
    database_url = os.environ.get("DATABASE_URL", "sqlite:///sprintwise.db")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get(
        "FLASK_SECRET_KEY", "sprintwise-dev-secret-change-in-production"
    )
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 900        # 15 minutes
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 604800    # 7 days

    if config:
        app.config.update(config)

    # --- Extensions ---
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # --- Register Blueprints ---
    from app.routes.auth import auth_bp
    from app.routes.sprints import sprint_bp
    from app.routes.tasks import task_bp
    from app.routes.timelogs import timelog_bp
    from app.routes.analytics import analytics_bp
    from app.routes.recommendations import rec_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.materials import materials_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(sprint_bp, url_prefix="/api/v1/sprints")
    app.register_blueprint(task_bp, url_prefix="/api/v1/tasks")
    app.register_blueprint(timelog_bp, url_prefix="/api/v1/timelogs")
    app.register_blueprint(analytics_bp, url_prefix="/api/v1/analytics")
    app.register_blueprint(rec_bp, url_prefix="/api/v1/recommendations")
    app.register_blueprint(dashboard_bp, url_prefix="/api/v1/dashboard")
    app.register_blueprint(materials_bp, url_prefix="/api/v1/materials")

    # Create tables & Check connectivity
    with app.app_context():
        try:
            db.create_all()
            # Basic connectivity check
            db.session.execute(text("SELECT 1"))
            print("✅ Database connection successful and tables verified.")
        except Exception as e:
            print(f"❌ DATABASE CONNECTION ERROR: {str(e)}")
            # Don't crash the app, but log it clearly

    return app
