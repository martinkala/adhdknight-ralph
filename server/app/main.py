from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import health, compute, auth, sync, migrate, user, config, monitoring, food_days, food_entries
from app.middleware.logging import RequestLoggingMiddleware
from app.db.database import engine, Base
from app.logging_config import configure_api_logging

configure_api_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        pass  # connection warmup check
    yield


app = FastAPI(
    title="ADHD Weight Vector Server",
    description=(
        "Backend server for ADHD behavioural index computation. "
        "Primary use: regression testing of the weight-vector algorithm without a mobile device. "
        "Secondary: future user data sync and web client support."
    ),
    version="0.1.0",
    contact={"name": "ADHD Tracker", "email": "martinkala@outlook.com"},
    openapi_tags=[
        {"name": "health", "description": "Server and DB health check"},
        {"name": "compute", "description": "ADHD index computation — identical to Android app algorithm"},
        {"name": "auth", "description": "Email + password authentication, JWT tokens"},
        {"name": "sync", "description": "Offline batch sync with LWW conflict resolution"},
        {"name": "migrate", "description": "Import historical Android data to server database"},
        {"name": "user", "description": "User profile and history for web client"},
        {"name": "config", "description": "Distributes the canonical entities.yaml per app_id, versioned"},
        {"name": "monitoring", "description": "Operator-facing synthetic check + integrity monitoring status"},
        {"name": "food", "description": "Food diary: days, entries and measurements of the logged-in user"},
    ],
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router)
app.include_router(compute.router)
app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(migrate.router)
app.include_router(user.router)
app.include_router(config.router)
app.include_router(monitoring.router)
app.include_router(food_days.router)
app.include_router(food_entries.router)
