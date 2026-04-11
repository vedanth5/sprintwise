"""
SprintWise - SQLAlchemy Models
"""
from datetime import datetime, date
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    academic_level = db.Column(db.String(50), nullable=False, default="undergraduate")
    weekly_study_target_hours = db.Column(db.Float, nullable=False, default=20.0)
    subjects = db.Column(db.Text, nullable=True)  # JSON array
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)

    sprints = db.relationship("Sprint", backref="user", lazy=True, cascade="all, delete-orphan")
    recommendations = db.relationship("Recommendation", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, plain: str):
        self.password_hash = generate_password_hash(plain)

    def check_password(self, plain: str) -> bool:
        return check_password_hash(self.password_hash, plain)

    def to_dict(self):
        import json
        return {
            "user_id": self.user_id,
            "email": self.email,
            "full_name": self.full_name,
            "academic_level": self.academic_level,
            "weekly_study_target_hours": self.weekly_study_target_hours,
            "subjects": json.loads(self.subjects) if self.subjects else [],
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat(),
        }


class Sprint(db.Model):
    __tablename__ = "sprints"
    __table_args__ = (
        db.Index("idx_sprints_user_id", "user_id", "start_date"),
    )

    sprint_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    tasks = db.relationship("Task", backref="sprint", lazy=True, cascade="all, delete-orphan")
    analytics_cache = db.relationship("AnalyticsCache", backref="sprint", uselist=False, cascade="all, delete-orphan")

    def get_duration_days(self):
        return (self.end_date - self.start_date).days + 1

    def to_dict(self, include_tasks=False):
        d = {
            "sprint_id": self.sprint_id,
            "user_id": self.user_id,
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status,
            "notes": self.notes,
            "duration_days": self.get_duration_days(),
            "created_at": self.created_at.isoformat(),
        }
        if include_tasks:
            d["tasks"] = [t.to_dict() for t in self.tasks]
        return d


class Task(db.Model):
    __tablename__ = "tasks"
    __table_args__ = (
        db.Index("idx_tasks_sprint_id", "sprint_id", "status"),
        db.Index("idx_tasks_user_subject", "user_id", "subject"),
    )

    task_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sprint_id = db.Column(db.Integer, db.ForeignKey("sprints.sprint_id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    estimated_minutes = db.Column(db.Integer, nullable=False, default=30)
    status = db.Column(db.String(20), nullable=False, default="pending")
    priority = db.Column(db.String(10), nullable=False, default="medium")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    time_logs = db.relationship("TimeLog", backref="task", lazy=True, cascade="all, delete-orphan")

    def get_total_time_spent_seconds(self):
        return sum(tl.duration_seconds or 0 for tl in self.time_logs if tl.end_time)

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "sprint_id": self.sprint_id,
            "user_id": self.user_id,
            "subject": self.subject,
            "description": self.description,
            "estimated_minutes": self.estimated_minutes,
            "status": self.status,
            "priority": self.priority,
            "total_time_spent_seconds": self.get_total_time_spent_seconds(),
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class TimeLog(db.Model):
    __tablename__ = "time_logs"
    __table_args__ = (
        db.Index("idx_timelogs_task_id", "task_id"),
        db.Index("idx_timelogs_user_date", "user_id", "start_time"),
    )

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)

    def stop_session(self):
        self.end_time = datetime.utcnow()
        self.duration_seconds = int((self.end_time - self.start_time).total_seconds())

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "task_id": self.task_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "is_active": self.end_time is None,
        }


class Recommendation(db.Model):
    __tablename__ = "recommendations"
    __table_args__ = (
        db.Index("idx_recs_user_dismissed", "user_id", "is_dismissed"),
    )

    rec_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    sprint_id = db.Column(db.Integer, db.ForeignKey("sprints.sprint_id", ondelete="SET NULL"), nullable=True)
    rule_id = db.Column(db.String(30), nullable=False)
    category = db.Column(db.String(20), nullable=False)  # productivity, subject, schedule, recovery
    priority = db.Column(db.String(10), nullable=False)   # high, medium, low
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_dismissed = db.Column(db.Boolean, nullable=False, default=False)

    def dismiss(self):
        self.is_dismissed = True

    def to_dict(self):
        return {
            "rec_id": self.rec_id,
            "rule_id": self.rule_id,
            "category": self.category,
            "priority": self.priority,
            "title": self.title,
            "body": self.body,
            "generated_at": self.generated_at.isoformat(),
            "is_dismissed": self.is_dismissed,
            "sprint_id": self.sprint_id,
        }


class AnalyticsCache(db.Model):
    __tablename__ = "analytics_cache"

    cache_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sprint_id = db.Column(db.Integer, db.ForeignKey("sprints.sprint_id", ondelete="CASCADE"), nullable=False, unique=True)
    completion_rate = db.Column(db.Float, nullable=True)
    consistency_index = db.Column(db.Float, nullable=True)
    subject_scores = db.Column(db.Text, nullable=True)  # JSON
    total_study_hours = db.Column(db.Float, nullable=True, default=0.0)
    trend_slope = db.Column(db.Float, nullable=True)
    computed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def is_stale(self, max_age_minutes=5):
        age = (datetime.utcnow() - self.computed_at).total_seconds() / 60
        return age > max_age_minutes

    def to_dict(self):
        import json
        return {
            "completion_rate": self.completion_rate,
            "consistency_index": self.consistency_index,
            "subject_scores": json.loads(self.subject_scores) if self.subject_scores else {},
            "total_study_hours": self.total_study_hours,
            "trend_slope": self.trend_slope,
            "computed_at": self.computed_at.isoformat(),
        }


class StudyMaterial(db.Model):
    __tablename__ = "study_materials"
    
    material_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text, nullable=True)  # AI-generated TL;DR
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    questions = db.relationship("GeneratedQuestion", backref="material", lazy=True, cascade="all, delete-orphan")
    mindmap = db.relationship("GeneratedMindmap", backref="material", uselist=False, cascade="all, delete-orphan")

    def to_dict(self, include_relations=False):
        d = {
            "material_id": self.material_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "summary": self.summary,
            "uploaded_at": self.uploaded_at.isoformat(),
        }
        if include_relations:
            d["questions"] = [q.to_dict() for q in self.questions]
            d["mindmap"] = self.mindmap.to_dict() if self.mindmap else None
        return d


class GeneratedQuestion(db.Model):
    __tablename__ = "generated_questions"

    question_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    material_id = db.Column(db.Integer, db.ForeignKey("study_materials.material_id", ondelete="CASCADE"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    suggested_answer = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "suggested_answer": self.suggested_answer
        }


class GeneratedMindmap(db.Model):
    __tablename__ = "generated_mindmaps"

    mindmap_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    material_id = db.Column(db.Integer, db.ForeignKey("study_materials.material_id", ondelete="CASCADE"), nullable=False, unique=True)
    mermaid_markup = db.Column(db.Text, nullable=False)
    
    def to_dict(self):
        return {
            "mindmap_id": self.mindmap_id,
            "mermaid_markup": self.mermaid_markup
        }
