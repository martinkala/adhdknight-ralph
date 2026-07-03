# ADHD Weight Vector Server

FastAPI server for computing the ADHD behavioural index — identical algorithm to the Android app.

**Primary purpose**: Regression testing of the weight-vector algorithm without a mobile device.

## Prerequisites

- Python 3.11+
- pip

## Quick Start

```bash
cd server
make dev
```

This will:
1. Verify Python 3.11+
2. Install dependencies from `requirements.txt`
3. Copy `.env.example` → `.env` if not present
4. Run Alembic migrations (SQLite by default)
5. Start Uvicorn on `http://localhost:8000`

## Running Tests

```bash
make test        # pytest (unit + API)
make test-bdd    # behave BDD feature files
make test-all    # both with coverage report
```

## API Documentation

Once running, open: **http://localhost:8000/docs**

### Key endpoints

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Compute daily index
curl -X POST http://localhost:8000/api/v1/compute/daily \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"1.0","date":"2026-06-30","entity_config":{"sleep":{"weight":15.0,"impact":1,"parent":null,"scale":true}},"values":[{"element_key":"sleep","value_binary":1,"value_scale":4}],"active_keys":["sleep"]}'

# Compute range (multiple days)
curl -X POST http://localhost:8000/api/v1/compute/range \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"1.0","entity_config":{"sleep":{"weight":15.0,"impact":1,"parent":null,"scale":true}},"days":[{"date":"2026-06-30","values":[{"element_key":"sleep","value_binary":1,"value_scale":5}],"active_keys":["sleep"]}]}'
```

## Configuration

Copy `.env.example` to `.env` and edit as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./dev.db` | Database connection string |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | JWT access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | JWT refresh token TTL |

## PostgreSQL Setup (optional)

```bash
# Install PostgreSQL driver
pip install asyncpg

# Set in .env:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/adhd_tracker
```

## Troubleshooting

**`python: command not found`** — use `python3` or ensure Python 3.11+ is on PATH.

**`alembic: command not found`** — run `pip install -r requirements.txt` first.

**`sqlite3.OperationalError: no such table`** — run `alembic upgrade head` or `make migrate`.

**Port 8000 already in use** — `lsof -ti:8000 | xargs kill` or change port in Makefile.
