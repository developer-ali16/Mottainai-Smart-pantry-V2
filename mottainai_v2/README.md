# 🥦 Mottainai Smart Pantry

> **Mottainai** (もったいない) — a Japanese concept expressing the feeling of regret when something useful is wasted.

A production-grade FastAPI backend that helps users track pantry inventory, monitor expiry dates, and receive timely reminders to reduce food waste.

---

## Features

| Category | What's included |
|---|---|
| **Auth** | JWT via HTTP-only cookie · Registration · Login/Logout · Email verification · Password reset · Change password |
| **Pantry** | Full CRUD · Pagination · Filter by category / expiry / search · Expiry heatmap summary |
| **Notifications** | In-app notifications · Unread count · Mark read/all-read · Email digest |
| **Scheduler** | Daily background job · Expiry reminders 1–3 days ahead · Duplicate prevention |
| **Security** | bcrypt hashing · Standard `exp` JWT claim · OWASP security headers · CSRF-safe cookies · User enumeration protection |
| **Observability** | Structured JSON logging · Request IDs · Per-request timing · Health + readiness probes |
| **Testing** | pytest · TestClient · SQLite in-memory fixtures · Unit + integration tests |
| **Deployment** | Dockerfile (multi-stage) · docker-compose · GitHub Actions CI/CD · Alembic migrations |

---

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/your-username/mottainai-smart-pantry.git
cd mottainai-smart-pantry

cp .env.example .env
# Edit .env: fill in SECRET_KEY (see below), optionally email settings

docker compose up --build
```

API → `http://localhost:8000`  
Interactive docs → `http://localhost:8000/docs`

### Manual

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in DATABASE_URL and SECRET_KEY

alembic upgrade head   # run migrations

uvicorn main:app --reload
```

### Generate a SECRET_KEY

```bash
openssl rand -hex 32
```

---

## API Reference

### Authentication
| Method | Endpoint | Auth Required |
|--------|----------|:---:|
| `POST` | `/api/v1/auth/register` | ✗ |
| `POST` | `/api/v1/auth/login` | ✗ |
| `POST` | `/api/v1/auth/logout` | ✓ |
| `GET` | `/api/v1/auth/me` | ✓ |
| `GET` | `/api/v1/auth/verify-email?token=...` | ✗ |
| `POST` | `/api/v1/auth/forgot-password` | ✗ |
| `POST` | `/api/v1/auth/reset-password` | ✗ |
| `POST` | `/api/v1/auth/change-password` | ✓ |

### Pantry
| Method | Endpoint | Auth Required |
|--------|----------|:---:|
| `GET` | `/api/v1/pantry/` | ✓ |
| `POST` | `/api/v1/pantry/` | ✓ |
| `GET` | `/api/v1/pantry/summary` | ✓ |
| `GET` | `/api/v1/pantry/{id}` | ✓ |
| `PUT` | `/api/v1/pantry/{id}` | ✓ |
| `DELETE` | `/api/v1/pantry/{id}` | ✓ |

### Notifications
| Method | Endpoint | Auth Required |
|--------|----------|:---:|
| `GET` | `/api/v1/notifications/` | ✓ |
| `GET` | `/api/v1/notifications/unread-count` | ✓ |
| `PATCH` | `/api/v1/notifications/read-all` | ✓ |
| `PATCH` | `/api/v1/notifications/{id}/read` | ✓ |

### Health
| Method | Endpoint |
|--------|----------|
| `GET` | `/api/v1/health` |
| `GET` | `/api/v1/health/ready` |

---

## Project Structure

```
mottainai-smart-pantry/
├── app/
│   ├── api/v1/          # Route handlers (thin — delegate to services)
│   │   ├── auth.py
│   │   ├── pantry.py
│   │   ├── notifications.py
│   │   └── health.py
│   ├── core/            # Config, security, logging, exceptions
│   ├── db/              # Engine, session, Base
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── repositories/    # Data access layer (SQL queries)
│   ├── services/        # Business logic layer
│   ├── middleware/      # Security headers, request logging
│   └── scheduler/       # APScheduler expiry reminder jobs
├── migrations/          # Alembic migration files
├── tests/
│   ├── unit/            # Schema and security unit tests
│   └── integration/     # Full request-cycle tests
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
└── requirements.txt
```

---

## Running Tests

```bash
# All tests
pytest tests/ -v --cov=app --cov-report=term-missing

# Unit tests only (no DB needed)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v
```

---

## Production Deployment

1. Set `APP_ENV=production` and `DEBUG=false`
2. Use a strong `SECRET_KEY` (minimum 32 characters)
3. Run migrations: `alembic upgrade head`
4. Start with Gunicorn:
   ```bash
   gunicorn main:app \
     --worker-class uvicorn.workers.UvicornWorker \
     --workers 4 \
     --bind 0.0.0.0:8000
   ```

---

## Tech Stack

- **Framework**: FastAPI 0.115
- **Database**: PostgreSQL via SQLAlchemy 2.0
- **Migrations**: Alembic
- **Auth**: PyJWT + passlib/bcrypt
- **Scheduler**: APScheduler
- **Testing**: pytest + httpx TestClient
- **Deployment**: Docker + Gunicorn/Uvicorn

---

## License

MIT
