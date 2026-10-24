# ADHD Tracker web console

Django-based web console (dashboard, trend, account) backed by the FastAPI
server in `../server/` — all data comes from the API, this app has no
tracking data of its own beyond Django sessions.

## Prerequisites

- Python 3.11+, Django 6 (`pip install -r requirements.txt`)
- The FastAPI server running (see `../server/README.md`)

## Quick start

```bash
cd web_app
cp .env.example .env   # edit FASTAPI_URL if the API isn't on the LAN dev default
python3 manage.py migrate
python3 manage.py runserver
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_DEBUG` | `true` | MUST be `false` in production |
| `DJANGO_ALLOWED_HOSTS` | empty | Comma-separated; `console.adhdknight.com` in production |
| `DJANGO_SECRET_KEY` | dev-only insecure default | Generate a real value for production |
| `DJANGO_DATABASE_URL` | unset (SQLite) | Postgres URL in production |
| `FASTAPI_URL` | LAN dev IP | **MUST** be `http://127.0.0.1:8095` in production — both services run on the same server; a LAN/dev IP here makes the console show "Server nie je dostupný" |

## Logging

Writes to `web_app/logs/web.log` (rotating, 10MB × 5 backups) — see the
`LOGGING` dict in `adhd_web/settings.py`. Kept separate from the FastAPI
server's `server/logs/api.log` so each service can be monitored
independently (feature 020, goal 4).

## Tests

```bash
python3 manage.py test core
```

## Production deployment

See `../server/README.md`'s "Produkčné nasadenie" section and
`../deploy/ansible/README.md` for the idempotent per-deploy playbook.
