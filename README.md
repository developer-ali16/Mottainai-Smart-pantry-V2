# Mottainai-Smart-pantry-V2 With Claude AI
Mottainai Smart Pantry — A production-ready FastAPI backend inspired by the Japanese concept of avoiding waste. Track pantry inventory, monitor expiry dates, and receive automated reminders before food goes bad.

<div align="center">

# 🥦 Mottainai Smart Pantry

**Mottainai** (もったいない) — *a Japanese concept expressing regret over waste.*

A production-ready FastAPI backend that helps users track pantry inventory,
monitor expiry dates, and receive automated reminders before food goes bad.

[![Python](https://img.shields.io/badge/Python-3.12-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ed?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

[Features](#-features) · [Quick Start](#-quick-start) · [API Reference](#-api-reference) · [Architecture](#-architecture) · [Deployment](#-production-deployment)

</div>

---

## 📖 About

Mottainai Smart Pantry is a backend API that solves a simple, real-world problem — food waste caused by forgotten or expired pantry items.

Users register, add items to their pantry with expiry dates, and a background scheduler automatically creates in-app notifications and sends digest emails as items approach expiry. The project is built to industry standards: layered architecture, JWT authentication, database migrations, structured logging, security headers, Docker support, and a full test suite.

---

## ✨ Features

| Area | What's included |
|---|---|
| **Authentication** | JWT via HTTP-only cookie · Register · Login / Logout · Email verification · Password reset · Change password |
| **Pantry Management** | Full CRUD · Pagination · Filter by category, expiry, or search · Expiry heatmap summary endpoint |
| **Notifications** | In-app notification feed · Unread count badge · Mark one / mark all as read · Email digest |
| **Background Scheduler** | Daily APScheduler job · Expiry warnings 1–3 days ahead · Duplicate-send prevention |
| **Security** | bcrypt password hashing · Standard `exp` JWT claim · OWASP security headers · CSRF-safe cookies · User enumeration protection |
| **Observability** | Structured JSON logging · Unique request IDs · Per-request timing · Liveness + readiness health probes |
| **Testing** | pytest · FastAPI TestClient · SQLite in-memory fixtures · Unit + integration test suites |
| **Deployment** | Multi-stage Dockerfile · docker-compose · GitHub Actions CI/CD · Alembic migrations |

---

## 🚀 Quick Start

### Option 1 — Docker (recommended)

```bash
# 1. Clone
git clone https://github.com/your-username/mottainai-smart-pantry.git
cd mottainai-smart-pantry

# 2. Configure
cp .env.example .env
# Open .env and set SECRET_KEY and DATABASE_URL

# 3. Run
docker compose up --build
```

| | URL |
|---|---|
| API | http://localhost:8000 |
| Interactive docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/v1/health |

---

### Option 2 — Local (without Docker)

**Prerequisites:** Python 3.12+, PostgreSQL

```bash
# 1. Virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Dependencies
pip install -r requirements.txt

# 3. Environment
cp .env.example .env
# Edit .env — set DATABASE_URL and SECRET_KEY at minimum

# 4. Database migrations
alembic upgrade head

# 5. Start server
uvicorn main:app --reload
```

---

### Generate a SECRET_KEY

```bash
openssl rand -hex 32
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and fill in your values.

| Variable | Required | Description |
|---|:---:|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | JWT signing key — minimum 32 characters |
| `ALGORITHM` | | JWT algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | Token lifetime (default: `60`) |
| `APP_ENV` | | `development` / `staging` / `production` |
| `ALLOWED_ORIGINS` | | Comma-separated CORS origins |
| `MAIL_USERNAME` | | Gmail address for sending emails |
| `MAIL_PASSWORD` | | Gmail App Password |
| `MAIL_FROM` | | Sender address |
| `EXPIRY_CHECK_DAYS_AHEAD` | | Days ahead to warn about expiry (default: `3`) |

> Email variables are optional. If not set, email features are gracefully disabled and the scheduler still creates in-app notifications.

---

## 📡 API Reference

Base URL: `/api/v1`

### 🔐 Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|:----:|---|
| `POST` | `/auth/register` | — | Create a new account |
| `POST` | `/auth/login` | — | Login and receive session cookie |
| `POST` | `/auth/logout` | ✓ | Clear session cookie |
| `GET` | `/auth/me` | ✓ | Get current user profile |
| `GET` | `/auth/verify-email?token=` | — | Verify email address |
| `POST` | `/auth/forgot-password` | — | Request password reset email |
| `POST` | `/auth/reset-password` | — | Apply reset token |
| `POST` | `/auth/change-password` | ✓ | Change password |

### 🥫 Pantry

| Method | Endpoint | Auth | Description |
|--------|----------|:----:|---|
| `GET` | `/pantry/` | ✓ | List items (paginated, filterable) |
| `POST` | `/pantry/` | ✓ | Add a new pantry item |
| `GET` | `/pantry/summary` | ✓ | Expiry heatmap (expired / today / 3d / 7d / 30d) |
| `GET` | `/pantry/{id}` | ✓ | Get a single item |
| `PUT` | `/pantry/{id}` | ✓ | Update an item |
| `DELETE` | `/pantry/{id}` | ✓ | Delete an item (`204 No Content`) |

**Query parameters for `GET /pantry/`:**

| Param | Type | Description |
|---|---|---|
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page, max 100 (default: 20) |
| `category` | string | Filter by category (e.g. `dairy`, `produce`) |
| `expiring_soon` | int | Items expiring within N days |
| `search` | string | Search by item name |

### 🔔 Notifications

| Method | Endpoint | Auth | Description |
|--------|----------|:----:|---|
| `GET` | `/notifications/` | ✓ | List notifications (paginated) |
| `GET` | `/notifications/unread-count` | ✓ | Get unread notification count |
| `PATCH` | `/notifications/{id}/read` | ✓ | Mark one notification as read |
| `PATCH` | `/notifications/read-all` | ✓ | Mark all notifications as read |

### 🏥 Health

| Method | Endpoint | Description |
|--------|----------|---|
| `GET` | `/health` | Liveness probe — is the server up? |
| `GET` | `/health/ready` | Readiness probe — is the database reachable? |

---

### Response Format

All endpoints return a consistent JSON envelope:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Pantry item added."
}
```

**Paginated list:**
```json
{
  "success": true,
  "data": [ ... ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Pantry item not found."
  }
}
```

---

## 🏗️ Architecture

```
mottainai-smart-pantry/
│
├── main.py                     # App factory + lifespan (startup/shutdown)
│
├── app/
│   ├── api/v1/                 # Route handlers — thin, delegate to services
│   │   ├── auth.py
│   │   ├── pantry.py
│   │   ├── notifications.py
│   │   └── health.py
│   │
│   ├── core/                   # Cross-cutting concerns
│   │   ├── config.py           # Pydantic BaseSettings
│   │   ├── security.py         # JWT + password hashing
│   │   ├── exceptions.py       # Custom exceptions + handlers
│   │   └── logging.py          # Structured JSON logging
│   │
│   ├── db/                     # Database engine + session
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── repositories/           # Data access layer (SQL only, no logic)
│   ├── services/               # Business logic layer
│   ├── middleware/             # Security headers + request logging
│   └── scheduler/              # APScheduler expiry reminder jobs
│
├── migrations/                 # Alembic migration files
│   └── versions/
│       └── 0001_initial.py
│
├── tests/
│   ├── conftest.py             # Fixtures + SQLite in-memory test DB
│   ├── unit/                   # Schema validation + security tests
│   └── integration/            # Full HTTP request-cycle tests
│
├── .env.example
├── .github/workflows/ci.yml    # GitHub Actions CI/CD
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml
├── alembic.ini
└── requirements.txt
```

**Layer responsibilities:**

```
Request → Router → Service → Repository → Database
                ↑               ↑
           (business         (SQL only,
            logic)           no logic)
```

- Routers validate input and delegate — no business logic
- Services own all business rules and orchestration
- Repositories own all SQL — no business logic
- Models are pure SQLAlchemy — no methods

---

## 🧪 Running Tests

Tests use an in-memory SQLite database — no external services required.

```bash
# Full suite with coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# Unit tests only (fastest)
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v
```

Test coverage target: **70%** (enforced in CI).

---

## 🐳 Production Deployment

### Using Gunicorn (recommended)

```bash
# 1. Set production environment
export APP_ENV=production
export DEBUG=false

# 2. Run database migrations
alembic upgrade head

# 3. Start server
gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
```

### Using Docker

```bash
# Build production image
docker build --target runtime -t mottainai:latest .

# Run
docker run -d \
  --env-file .env \
  -p 8000:8000 \
  mottainai:latest
```

### Production checklist

- [ ] `APP_ENV=production` set
- [ ] `DEBUG=false`
- [ ] Strong `SECRET_KEY` (32+ characters, generated with `openssl rand -hex 32`)
- [ ] `ALLOWED_ORIGINS` set to your actual frontend domain
- [ ] `alembic upgrade head` run before first start
- [ ] Cookie `secure=True` is automatic when `APP_ENV=production`
- [ ] Swagger docs (`/docs`) are disabled automatically in production

---

## 🔒 Security

- Passwords hashed with **bcrypt** via passlib
- JWT signed with HS256, validated expiry using standard `exp` claim
- Auth cookie is `httponly=True`, `secure=True` (production), `samesite=lax`
- Login returns identical error for wrong email or wrong password — prevents user enumeration
- OWASP security headers on every response (`X-Content-Type-Options`, `X-Frame-Options`, `HSTS`, `CSP`, `Referrer-Policy`)
- Secrets managed via environment variables — never hardcoded

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| Language | Python 3.12 |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Auth | PyJWT + passlib/bcrypt |
| Scheduler | APScheduler 3.x |
| Validation | Pydantic v2 |
| Testing | pytest + httpx TestClient |
| Server | Uvicorn / Gunicorn |
| Containerisation | Docker + docker-compose |
| CI/CD | GitHub Actions |

---

## 🤝 Contributing

```bash
# Fork → clone → create feature branch
git checkout -b feature/your-feature

# Make changes, add tests
pytest tests/ -v

# Commit and push
git push origin feature/your-feature

# Open a pull request
```

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ and inspired by もったいない

</div>
