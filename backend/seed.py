"""
SprintWise - Database Seeder
Creates a demo user with sample sprints, tasks, and time logs for testing.

Usage:
  cd backend
  python seed.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, date, timedelta
import json

from app import create_app, db
from app.models import User, Sprint, Task, TimeLog, AnalyticsCache
from app.services.analytics import AnalyticsEngine

app = create_app()

SUBJECTS = ["Mathematics", "Physics", "Chemistry", "Computer Science"]

TASK_TEMPLATES = {
    "Mathematics": [
        "Solve integration problems – Chapter 5",
        "Revise differentiation formulas",
        "Practice limits and continuity",
        "Complete matrix algebra exercises",
        "Attempt past year question paper",
    ],
    "Physics": [
        "Study thermodynamics – Laws 1 & 2",
        "Revise electric field problems",
        "Solve optics problems (refraction)",
        "Complete oscillations notes",
        "Attempt numerical problems – Chapter 8",
    ],
    "Chemistry": [
        "Memorise periodic table trends",
        "Practice organic reaction mechanisms",
        "Revise chemical equilibrium chapter",
        "Complete electrochemistry notes",
        "Attempt previous semester questions",
    ],
    "Computer Science": [
        "Implement binary search tree",
        "Study sorting algorithms (merge, quick)",
        "Revise database normalization (1NF-3NF)",
        "Complete OS process scheduling notes",
        "Practice SQL query problems",
    ]
}

def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✓ Database reset")

        # ── Demo User ──
        user = User(
            email="demo@sprintwise.com",
            full_name="Alex Kumar",
            academic_level="undergraduate",
            weekly_study_target_hours=25.0,
            subjects=json.dumps(SUBJECTS),
        )
        user.set_password("demo1234")
        db.session.add(user)
        db.session.flush()
        print(f"✓ Created demo user: demo@sprintwise.com / demo1234")

        # ── Completed Sprints (3 historical) ──
        today = date.today()
        sprint_history = []

        for i in range(3, 0, -1):
            start = today - timedelta(days=i * 8 + 7)
            end = today - timedelta(days=i * 8)
            sprint = Sprint(
                user_id=user.user_id,
                name=f"Sprint {4 - i} – Exam Prep",
                start_date=start,
                end_date=end,
                status="completed",
                notes=f"Focus on covering chapters {i * 2 - 1} and {i * 2} across all subjects",
            )
            db.session.add(sprint)
            db.session.flush()

            # Add tasks with varying completion rates (60%, 72%, 85%)
            completion_targets = [0.60, 0.72, 0.85]
            target = completion_targets[3 - i - 1]
            tasks_added = []

            for subj in SUBJECTS:
                templates = TASK_TEMPLATES[subj][:4]
                for j, desc in enumerate(templates):
                    task = Task(
                        sprint_id=sprint.sprint_id,
                        user_id=user.user_id,
                        subject=subj,
                        description=desc,
                        estimated_minutes=45,
                        priority=["high", "medium", "medium", "low"][j % 4],
                    )
                    db.session.add(task)
                    tasks_added.append(task)

            db.session.flush()

            # Mark tasks complete according to target
            n_complete = int(len(tasks_added) * target)
            for task in tasks_added[:n_complete]:
                task.status = "completed"
                task.completed_at = datetime.combine(
                    start + timedelta(days=j % sprint.get_duration_days()),
                    datetime.min.time()
                ).replace(hour=14)

                # Add time log
                log = TimeLog(
                    task_id=task.task_id,
                    user_id=user.user_id,
                    start_time=task.completed_at - timedelta(minutes=40),
                    end_time=task.completed_at,
                    duration_seconds=2400,
                )
                db.session.add(log)

            sprint_history.append(sprint)

        db.session.commit()

        # Compute analytics for historical sprints
        for sprint in sprint_history:
            AnalyticsEngine.compute_sprint_metrics(sprint.sprint_id, user.user_id, force_refresh=True)
        print("✓ Created 3 completed historical sprints with analytics")

        # ── Active Sprint ──
        active_start = today - timedelta(days=3)
        active_end = today + timedelta(days=3)
        active = Sprint(
            user_id=user.user_id,
            name="Sprint 4 – Final Revision",
            start_date=active_start,
            end_date=active_end,
            status="active",
            notes="Final push before semester exams. Cover all weak areas identified in Sprint 3.",
        )
        db.session.add(active)
        db.session.flush()

        # Add 16 tasks across 4 subjects
        active_tasks = []
        for subj in SUBJECTS:
            for j, desc in enumerate(TASK_TEMPLATES[subj]):
                task = Task(
                    sprint_id=active.sprint_id,
                    user_id=user.user_id,
                    subject=subj,
                    description=desc,
                    estimated_minutes=[30, 45, 60, 30, 90][j % 5],
                    priority=["high", "high", "medium", "medium", "low"][j % 5],
                )
                db.session.add(task)
                active_tasks.append(task)

        db.session.flush()

        # Complete about 45% of active sprint tasks
        for task in active_tasks[:7]:
            task.status = "completed"
            task.completed_at = datetime.combine(
                active_start + timedelta(days=1),
                datetime.min.time()
            ).replace(hour=10)
            log = TimeLog(
                task_id=task.task_id,
                user_id=user.user_id,
                start_time=task.completed_at - timedelta(minutes=35),
                end_time=task.completed_at,
                duration_seconds=2100,
            )
            db.session.add(log)

        # One in-progress task
        active_tasks[7].status = "in_progress"

        db.session.commit()

        # Compute active sprint metrics
        AnalyticsEngine.compute_sprint_metrics(active.sprint_id, user.user_id, force_refresh=True)
        print(f"✓ Created active sprint with {len(active_tasks)} tasks (7 completed, 1 in-progress)")

        print("\n" + "="*50)
        print("  SEED COMPLETE")
        print("="*50)
        print("  Login: demo@sprintwise.com")
        print("  Password: demo1234")
        print("  Database: instance/sprintwise.db")
        print("="*50)

if __name__ == "__main__":
    seed()
