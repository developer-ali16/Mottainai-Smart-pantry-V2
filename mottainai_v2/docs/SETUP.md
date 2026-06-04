# Mottainai Smart Pantry — Setup Guide

## Quick Start (Docker)

```bash
# 1. Clone the repo
git clone https://github.com/your-username/mottainai-smart-pantry.git
cd mottainai-smart-pantry

# 2. Configure environment
cp .env.example .env
# Edit .env and fill in your values (see comments inside)

# 3. Start with Docker Compose
docker compose up --build

# API is available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

## Manual Setup (without Docker)

```bash
# 1. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — minimum required: DATABASE_URL and SECRET_KEY

# 4. Run database migrations
alembic upgrade head

# 5. Start the server
uvicorn main:app --reload
```

## Generating a SECRET_KEY

```bash
openssl rand -hex 32
```

## Running Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/v1/auth/register | No | Create account |
| POST | /api/v1/auth/login | No | Login (sets cookie) |
| POST | /api/v1/auth/logout | Yes | Clear session |
| GET | /api/v1/auth/me | Yes | Current user profile |
| GET | /api/v1/auth/verify-email | No | Verify email token |
| POST | /api/v1/auth/forgot-password | No | Request reset email |
| POST | /api/v1/auth/reset-password | No | Apply reset token |
| POST | /api/v1/auth/change-password | Yes | Change password |
| GET | /api/v1/pantry/ | Yes | List items (paginated) |
| POST | /api/v1/pantry/ | Yes | Add item |
| GET | /api/v1/pantry/summary | Yes | Expiry heatmap |
| GET | /api/v1/pantry/{id} | Yes | Get single item |
| PUT | /api/v1/pantry/{id} | Yes | Update item |
| DELETE | /api/v1/pantry/{id} | Yes | Delete item (204) |
| GET | /api/v1/notifications/ | Yes | List notifications |
| GET | /api/v1/notifications/unread-count | Yes | Unread count |
| PATCH | /api/v1/notifications/{id}/read | Yes | Mark one read |
| PATCH | /api/v1/notifications/read-all | Yes | Mark all read |
| GET | /api/v1/health | No | Liveness probe |
| GET | /api/v1/health/ready | No | Readiness probe |

## Environment Variables

See `.env.example` for full documentation of all variables.

## Production Deployment

1. Set `APP_ENV=production` in your environment.
2. Set `DEBUG=false`.
3. Use a strong `SECRET_KEY` (minimum 32 characters).
4. Run `alembic upgrade head` before starting the server.
5. Use Gunicorn with Uvicorn workers:
   ```
   gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
   ```
