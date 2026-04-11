"""
SprintWise - Test Suite
Run: cd backend && pytest tests/ -v
"""
import pytest
import json
from app import create_app, db as _db


@pytest.fixture(scope="session")
def app():
    test_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret",
        "JWT_ACCESS_TOKEN_EXPIRES": 9999,
    })
    with test_app.app_context():
        _db.create_all()
        yield test_app
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()


def register_and_login(client, email="test@example.com", password="password123"):
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test User",
        "weekly_study_target_hours": 20
    })
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    data = res.get_json()
    return data.get("access_token"), data.get("user", {}).get("user_id")


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────
# AUTH TESTS
# ─────────────────────────────────────────
class TestAuth:
    def test_register_success(self, client):
        res = client.post("/api/v1/auth/register", json={
            "email": "newuser@test.com",
            "password": "securepass1",
            "full_name": "New User"
        })
        assert res.status_code == 201
        data = res.get_json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@test.com"

    def test_register_duplicate_email(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "dup@test.com", "password": "pass1234", "full_name": "Dup"
        })
        res = client.post("/api/v1/auth/register", json={
            "email": "dup@test.com", "password": "pass1234", "full_name": "Dup"
        })
        assert res.status_code == 409

    def test_register_short_password(self, client):
        res = client.post("/api/v1/auth/register", json={
            "email": "short@test.com", "password": "abc", "full_name": "Short"
        })
        assert res.status_code == 400

    def test_login_success(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "login@test.com", "password": "loginpass", "full_name": "Login User"
        })
        res = client.post("/api/v1/auth/login", json={
            "email": "login@test.com", "password": "loginpass"
        })
        assert res.status_code == 200
        assert "access_token" in res.get_json()

    def test_login_wrong_password(self, client):
        res = client.post("/api/v1/auth/login", json={
            "email": "login@test.com", "password": "wrongpass"
        })
        assert res.status_code == 401

    def test_protected_route_no_token(self, client):
        res = client.get("/api/v1/sprints/")
        assert res.status_code == 401

    def test_me_endpoint(self, client):
        token, _ = register_and_login(client, "me@test.com", "mepassword1")
        res = client.get("/api/v1/auth/me", headers=auth_header(token))
        assert res.status_code == 200
        assert res.get_json()["user"]["email"] == "me@test.com"

    def test_profile_update(self, client):
        token, _ = register_and_login(client, "profile@test.com", "profile123")
        res = client.put("/api/v1/auth/profile", json={
            "weekly_study_target_hours": 25,
            "subjects": ["Math", "Physics"]
        }, headers=auth_header(token))
        assert res.status_code == 200
        data = res.get_json()
        assert data["user"]["weekly_study_target_hours"] == 25
        assert "Math" in data["user"]["subjects"]


# ─────────────────────────────────────────
# SPRINT TESTS
# ─────────────────────────────────────────
class TestSprints:
    def test_create_sprint(self, client):
        token, _ = register_and_login(client, "sprint@test.com", "sprint123")
        res = client.post("/api/v1/sprints/", json={
            "name": "Week 1 Sprint",
            "start_date": "2025-02-01",
            "end_date": "2025-02-07"
        }, headers=auth_header(token))
        assert res.status_code == 201
        data = res.get_json()
        assert data["sprint"]["name"] == "Week 1 Sprint"
        assert data["sprint"]["status"] == "active"

    def test_create_sprint_invalid_dates(self, client):
        token, _ = register_and_login(client, "sprint2@test.com", "sprint123")
        res = client.post("/api/v1/sprints/", json={
            "name": "Bad Sprint",
            "start_date": "2025-02-07",
            "end_date": "2025-02-01"
        }, headers=auth_header(token))
        assert res.status_code == 400

    def test_list_sprints(self, client):
        token, _ = register_and_login(client, "sprintlist@test.com", "sprint123")
        client.post("/api/v1/sprints/", json={
            "name": "Sprint A", "start_date": "2025-01-01", "end_date": "2025-01-07"
        }, headers=auth_header(token))
        res = client.get("/api/v1/sprints/", headers=auth_header(token))
        assert res.status_code == 200
        assert len(res.get_json()["sprints"]) >= 1

    def test_sprint_isolation(self, client):
        """User A cannot access User B's sprints."""
        token_a, _ = register_and_login(client, "usera@test.com", "passworda1")
        token_b, _ = register_and_login(client, "userb@test.com", "passwordb1")

        res = client.post("/api/v1/sprints/", json={
            "name": "User A Sprint", "start_date": "2025-03-01", "end_date": "2025-03-07"
        }, headers=auth_header(token_a))
        sprint_id = res.get_json()["sprint"]["sprint_id"]

        # User B tries to access User A's sprint
        res_b = client.get(f"/api/v1/sprints/{sprint_id}", headers=auth_header(token_b))
        assert res_b.status_code == 404

    def test_delete_sprint_cascades(self, client):
        token, _ = register_and_login(client, "cascade@test.com", "cascade123")
        sprint_res = client.post("/api/v1/sprints/", json={
            "name": "Delete Me", "start_date": "2025-04-01", "end_date": "2025-04-07"
        }, headers=auth_header(token))
        sprint_id = sprint_res.get_json()["sprint"]["sprint_id"]

        client.post("/api/v1/tasks/", json={
            "sprint_id": sprint_id, "subject": "Math",
            "description": "Task to delete", "estimated_minutes": 30
        }, headers=auth_header(token))

        del_res = client.delete(f"/api/v1/sprints/{sprint_id}", headers=auth_header(token))
        assert del_res.status_code == 200

        tasks_res = client.get(f"/api/v1/tasks/sprint/{sprint_id}", headers=auth_header(token))
        assert tasks_res.status_code == 404


# ─────────────────────────────────────────
# TASK TESTS
# ─────────────────────────────────────────
class TestTasks:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.token, _ = register_and_login(client, "tasks@test.com", "tasks1234")
        res = client.post("/api/v1/sprints/", json={
            "name": "Task Sprint", "start_date": "2025-05-01", "end_date": "2025-05-07"
        }, headers=auth_header(self.token))
        self.sprint_id = res.get_json()["sprint"]["sprint_id"]
        self.client = client

    def test_create_task(self):
        res = self.client.post("/api/v1/tasks/", json={
            "sprint_id": self.sprint_id, "subject": "Physics",
            "description": "Chapter 3 review", "estimated_minutes": 45, "priority": "high"
        }, headers=auth_header(self.token))
        assert res.status_code == 201
        assert res.get_json()["task"]["subject"] == "Physics"

    def test_task_status_transition(self):
        task_res = self.client.post("/api/v1/tasks/", json={
            "sprint_id": self.sprint_id, "subject": "Math",
            "description": "Algebra", "estimated_minutes": 30
        }, headers=auth_header(self.token))
        task_id = task_res.get_json()["task"]["task_id"]

        res = self.client.patch(f"/api/v1/tasks/{task_id}", json={"status": "completed"},
                                headers=auth_header(self.token))
        assert res.status_code == 200
        assert res.get_json()["task"]["status"] == "completed"
        assert res.get_json()["task"]["completed_at"] is not None

    def test_invalid_status_rejected(self):
        task_res = self.client.post("/api/v1/tasks/", json={
            "sprint_id": self.sprint_id, "subject": "Chem",
            "description": "Balancing equations", "estimated_minutes": 20
        }, headers=auth_header(self.token))
        task_id = task_res.get_json()["task"]["task_id"]
        res = self.client.patch(f"/api/v1/tasks/{task_id}", json={"status": "flying"},
                                headers=auth_header(self.token))
        assert res.status_code == 400

    def test_bulk_create(self):
        res = self.client.post("/api/v1/tasks/bulk", json={
            "sprint_id": self.sprint_id,
            "tasks": [
                {"subject": "Bio", "description": f"Task {i}", "estimated_minutes": 30}
                for i in range(5)
            ]
        }, headers=auth_header(self.token))
        assert res.status_code == 201
        assert len(res.get_json()["tasks"]) == 5


# ─────────────────────────────────────────
# TIME TRACKING TESTS
# ─────────────────────────────────────────
class TestTimeLogs:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.token, _ = register_and_login(client, "time@test.com", "timelog12")
        sprint_res = client.post("/api/v1/sprints/", json={
            "name": "Time Sprint", "start_date": "2025-06-01", "end_date": "2025-06-07"
        }, headers=auth_header(self.token))
        sprint_id = sprint_res.get_json()["sprint"]["sprint_id"]
        task_res = client.post("/api/v1/tasks/", json={
            "sprint_id": sprint_id, "subject": "CS", "description": "Algorithms", "estimated_minutes": 60
        }, headers=auth_header(self.token))
        self.task_id = task_res.get_json()["task"]["task_id"]
        self.client = client

    def test_start_stop_session(self):
        start_res = self.client.post("/api/v1/timelogs/start", json={"task_id": self.task_id},
                                     headers=auth_header(self.token))
        assert start_res.status_code == 201
        log_id = start_res.get_json()["log"]["log_id"]

        stop_res = self.client.post("/api/v1/timelogs/stop", json={"log_id": log_id},
                                    headers=auth_header(self.token))
        assert stop_res.status_code == 200
        assert stop_res.get_json()["log"]["duration_seconds"] >= 0

    def test_duplicate_session_prevention(self):
        self.client.post("/api/v1/timelogs/start", json={"task_id": self.task_id},
                         headers=auth_header(self.token))
        res2 = self.client.post("/api/v1/timelogs/start", json={"task_id": self.task_id},
                                headers=auth_header(self.token))
        # Should return 200 (existing session) not 201 (new session)
        assert res2.status_code == 200


# ─────────────────────────────────────────
# ANALYTICS ENGINE TESTS
# ─────────────────────────────────────────
class TestAnalyticsEngine:
    def test_completion_rate_all_complete(self, client):
        from app.services.analytics import AnalyticsEngine
        token, _ = register_and_login(client, "analytics@test.com", "analytics1")
        sprint_res = client.post("/api/v1/sprints/", json={
            "name": "Analytics Sprint", "start_date": "2025-07-01", "end_date": "2025-07-07"
        }, headers=auth_header(token))
        sprint_id = sprint_res.get_json()["sprint"]["sprint_id"]

        # Create 4 tasks, complete all
        task_ids = []
        for i in range(4):
            tr = client.post("/api/v1/tasks/", json={
                "sprint_id": sprint_id, "subject": "Math",
                "description": f"Task {i}", "estimated_minutes": 30
            }, headers=auth_header(token))
            task_ids.append(tr.get_json()["task"]["task_id"])

        for tid in task_ids:
            client.patch(f"/api/v1/tasks/{tid}", json={"status": "completed"},
                         headers=auth_header(token))

        res = client.get(f"/api/v1/analytics/sprint/{sprint_id}", headers=auth_header(token))
        assert res.status_code == 200
        assert res.get_json()["metrics"]["completion_rate"] == 100.0

    def test_completion_rate_zero_tasks(self, client):
        token, _ = register_and_login(client, "zeroanal@test.com", "zeroanal1")
        sprint_res = client.post("/api/v1/sprints/", json={
            "name": "Empty Sprint", "start_date": "2025-08-01", "end_date": "2025-08-07"
        }, headers=auth_header(token))
        sprint_id = sprint_res.get_json()["sprint"]["sprint_id"]
        res = client.get(f"/api/v1/analytics/sprint/{sprint_id}", headers=auth_header(token))
        # None is returned for sprints with no tasks
        assert res.get_json()["metrics"]["completion_rate"] is None

    def test_dashboard_summary_structure(self, client):
        token, _ = register_and_login(client, "dash@test.com", "dashboard1")
        res = client.get("/api/v1/dashboard/summary", headers=auth_header(token))
        assert res.status_code == 200
        data = res.get_json()
        # Verify all required fields present
        for key in ["active_sprint", "sprint_trend", "subject_scores",
                    "consistency_index", "total_study_hours_week",
                    "study_streak_days", "recommendations", "stats"]:
            assert key in data, f"Missing key: {key}"
