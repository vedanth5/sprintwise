# ⚡ SprintWise

### AI-Powered Student Productivity and Sprint Management System

> Plan smarter. Study consistently. Improve daily.

SprintWise adapts **Agile sprint methodology** to student academic workflows. Plan weekly study sprints, track tasks and time, analyse performance across subjects, and receive personalised AI recommendations — all in one self-hosted, privacy-first platform.

---

## 📸 Features

| Feature | Description |
|---|---|
| 🏃 **Sprint Planning** | Create time-boxed study sprints with subjects, tasks, and goals |
| ✅ **Task Tracking** | Complete tasks, track in-progress work, bulk-add tasks |
| ⏱️ **Time Logging** | Per-task study session timer with start/stop |
| 📊 **Performance Analytics** | Completion rate, consistency index, subject scores, trend analysis |
| 🤖 **AI Recommendations** | 12-rule engine generating personalised study improvement suggestions |
| 🎯 **Next Task Suggestion** | AI-prioritised next task based on subject urgency and sprint pressure |
| 📈 **Dashboard** | Visual overview with charts, streaks, and progress bars |
| 🔐 **JWT Auth** | Secure per-user authentication with refresh tokens |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Chart.js 4, Axios |
| Backend | Python 3.11, Flask 3.x |
| ORM | SQLAlchemy 2.x |
| Auth | Flask-JWT-Extended (JWT / HttpOnly cookies) |
| Database | SQLite (dev) / PostgreSQL or MySQL (prod) |
| AI Engine | Custom Python rule engine + statistics module |
| Deployment | Docker + Docker Compose |

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/yourusername/sprintwise.git
cd sprintwise

# Start everything
docker-compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
```

### Option 2: Manual Setup

#### Backend

```bash
# 1. Navigate to backend
cd backend

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables (copy and edit .env)
cp .env .env.local
# Edit .env with your SECRET_KEY

# 5. Initialise the database
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# 6. (Optional) Seed with demo data
python seed.py

# 7. Run the server
python app.py
# OR: flask run --port 5000
```

#### Frontend

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start the development server
npm start

# Opens http://localhost:3000
```

---

## 🌱 Demo Credentials (after seeding)

```
Email:    demo@sprintwise.com
Password: demo1234
```

The seeder creates:
- 3 completed historical sprints (60%, 72%, 85% completion rates)
- 1 active sprint with tasks in various states
- Pre-computed analytics and AI recommendations

---

## 🔑 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FLASK_SECRET_KEY` | *(required in prod)* | JWT signing key |
| `DATABASE_URL` | `sqlite:///sprintwise.db` | Database connection string |
| `JWT_ACCESS_TOKEN_EXPIRES` | `900` | Access token TTL (seconds) |
| `JWT_REFRESH_TOKEN_EXPIRES` | `604800` | Refresh token TTL (7 days) |
| `FLASK_ENV` | `development` | `development` or `production` |
| `PORT` | `5000` | Backend port |

For PostgreSQL: `DATABASE_URL=postgresql://user:pass@localhost:5432/sprintwise`

---

## 📁 Project Structure

```
sprintwise/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── models/
│   │   │   └── __init__.py      # SQLAlchemy models (User, Sprint, Task, TimeLog, etc.)
│   │   ├── routes/
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── sprints.py       # Sprint CRUD
│   │   │   ├── tasks.py         # Task CRUD + bulk create
│   │   │   ├── timelogs.py      # Time tracking
│   │   │   ├── analytics.py     # Analytics endpoints
│   │   │   ├── recommendations.py # AI recommendation endpoints
│   │   │   └── dashboard.py     # Dashboard aggregation
│   │   └── services/
│   │       ├── analytics.py     # AnalyticsEngine (completion, consistency, subjects, trend)
│   │       └── recommendations.py # RecommendationEngine (12 rules, next-task suggestion)
│   ├── tests/
│   │   └── test_sprintwise.py   # Full pytest test suite
│   ├── app.py                   # Application entry point
│   ├── seed.py                  # Demo data seeder
│   ├── requirements.txt
│   ├── .env
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.js               # Router and layout
│   │   ├── index.css            # Global styles
│   │   ├── context/
│   │   │   └── AuthContext.js   # Global auth state
│   │   ├── services/
│   │   │   └── api.js           # Axios API client with interceptors
│   │   ├── components/
│   │   │   └── Layout.js        # Sidebar + page shell
│   │   └── pages/
│   │       ├── AuthPage.js      # Login / Register
│   │       ├── Dashboard.js     # Main dashboard
│   │       ├── SprintsPage.js   # Sprint listing
│   │       ├── SprintDetail.js  # Sprint + tasks + analytics
│   │       ├── AnalyticsPage.js # History charts
│   │       └── ProfilePage.js   # User settings
│   ├── public/index.html
│   ├── package.json
│   └── Dockerfile
├── docs/
│   └── test_api.sh              # Shell-based API test suite
├── docker-compose.yml
└── README.md
```

---

## 🔌 API Reference

All endpoints require `Authorization: Bearer <token>` except `/auth/register` and `/auth/login`.

### Authentication
```
POST /api/v1/auth/register        Register new user
POST /api/v1/auth/login           Login → access + refresh tokens
POST /api/v1/auth/refresh         Refresh access token
GET  /api/v1/auth/me              Get current user
PUT  /api/v1/auth/profile         Update profile
```

### Sprints
```
GET    /api/v1/sprints/           List user's sprints
POST   /api/v1/sprints/           Create sprint
GET    /api/v1/sprints/:id        Get sprint with tasks
PUT    /api/v1/sprints/:id        Update sprint
PATCH  /api/v1/sprints/:id/complete  Complete sprint
DELETE /api/v1/sprints/:id        Delete sprint (cascade)
```

### Tasks
```
POST   /api/v1/tasks/             Create task
POST   /api/v1/tasks/bulk         Bulk create tasks
GET    /api/v1/tasks/sprint/:id   Get sprint tasks
PATCH  /api/v1/tasks/:id          Update task (status, priority, etc.)
DELETE /api/v1/tasks/:id          Delete task
```

### Time Tracking
```
POST   /api/v1/timelogs/start     Start timer for a task
POST   /api/v1/timelogs/stop      Stop active timer
GET    /api/v1/timelogs/task/:id  Get logs for a task
GET    /api/v1/timelogs/active    Get all active sessions
```

### Analytics
```
GET    /api/v1/analytics/sprint/:id   Sprint metrics
GET    /api/v1/analytics/history      Historical sprint data
GET    /api/v1/analytics/anomaly      Z-score anomaly detection
```

### Recommendations & Dashboard
```
GET    /api/v1/recommendations/       Get top 3 active recommendations
PATCH  /api/v1/recommendations/:id/dismiss  Dismiss recommendation
GET    /api/v1/dashboard/summary      Full dashboard payload
```

---

## 🧪 Running Tests

```bash
cd backend

# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test class
pytest tests/test_sprintwise.py::TestAnalyticsEngine -v

# API integration tests (requires running server)
cd ../docs
chmod +x test_api.sh && ./test_api.sh
```

---

## 🤖 AI Recommendation Engine

The AI engine evaluates **12 rules** across 4 categories without any external API:

| Category | Rules | Trigger |
|---|---|---|
| **Productivity** | R-P01, R-P02, R-P04 | Low completion, inactivity, declining trend |
| **Subject** | R-S01, R-S02, R-S03 | Weak subject, under-investment, overemphasis |
| **Schedule** | R-SC01, R-SC02, R-SC03 | Low consistency, cramming, no active sprint |
| **Recovery** | R-RC01 | Performance improvement after decline |

Rules are evaluated on every dashboard load. Deduplication prevents repeat notifications.

---

## 📊 Analytics Algorithms

- **Completion Rate**: `(completed_tasks / total_tasks) × 100`
- **Consistency Index**: `unique_study_days / sprint_duration_days`
- **Subject Score**: `(completion_rate × 0.6) + (time_score × 0.4)`
- **Trend Slope**: Linear regression on last 4 sprint completion rates
- **Anomaly Detection**: Z-score vs. user's own historical mean (threshold: −1.5σ)
- **Next Task Score**: `(priority_weight × 0.4) + (subject_urgency × 0.35) + (time_pressure × 0.25)`

---

## 🔒 Security

- Passwords hashed with PBKDF2-SHA256 (Werkzeug default: 260,000 iterations)
- JWT access tokens expire in 15 minutes; refresh tokens in 7 days
- All protected routes verify resource ownership (no IDOR possible)
- SQLAlchemy parameterised queries prevent SQL injection
- Marshmallow schemas validate all incoming payloads

---

## 📈 Future Roadmap

- [ ] Push notifications via Web Push API
- [ ] Spaced repetition flashcard module (SM-2 algorithm)
- [ ] Natural language task entry (NLP parser)
- [ ] Mobile apps (React Native)
- [ ] Group sprint mode with peer accountability
- [ ] LMS integration (Moodle, Canvas)
- [ ] Machine learning recommendation engine (contextual bandit)

---

## 📄 License

MIT — see `LICENSE` for details.

---

*SprintWise – Final Year Engineering Project | Department of Computer Engineering*
