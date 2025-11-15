from contextlib import asynccontextmanager
from typing import Generator
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .core.db import SessionLocal
from .core import logging as core_logging
from .core.config import settings
from .api.routes_campaigns import router as campaigns_router
from .api.routes_assets import router as assets_router
from .api.routes_brands import router as brands_router
from .api.routes_workflows import router as workflows_router

def get_db() -> Generator[Session, None, None]:
    """SQLAlchemy session dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context for startup/shutdown.
    Good place to initialize logging, verify DB connectivity, warm caches, etc.
    """
    # Configure structured logging once at startup
    core_logging.configure_logging()

    # You could put a lightweight DB health check here if desired
    # e.g., with SessionLocal() as db: db.execute(text("SELECT 1"))

    yield

    # Any async shutdown hooks (flush metrics, close clients, etc.) go here.


app = FastAPI(
    title=getattr(settings, "APP_NAME", "Creative Automation POC"),
    version=getattr(settings, "APP_VERSION", "0.1.0"),
    lifespan=lifespan,
)

# CORS config, allow all for now
cors_origins = getattr(settings, "BACKEND_CORS_ORIGINS", ["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# exceptions
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catch-all safeguard so POC doesn't return HTML stack traces.
    In production, you'd map specific exceptions to clear error codes.
    """
    # You can add structured logging here using your core logging utilities
    # e.g., logger.exception("Unhandled error", extra={...})
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": exc.__class__.__name__,
        },
    )


# --- Routers --------------------------------------------------------------------

app.include_router(
    campaigns_router,
    prefix="/campaigns",
    tags=["campaigns"],
    dependencies=[Depends(get_db)],
)

app.include_router(
    assets_router,
    prefix="/assets",
    tags=["assets"],
    dependencies=[Depends(get_db)],
)

app.include_router(
    brands_router,
    prefix="/brands",
    tags=["brands"],
    dependencies=[Depends(get_db)],
)

app.include_router(
    workflows_router,
    prefix="/workflows",
    tags=["workflows"],
    dependencies=[Depends(get_db)],
)

# health endpoint
@app.get("/healthz", tags=["system"])
async def healthcheck() -> dict:
    """
    Lightweight health endpoint for container/orchestrator checks.
    For deeper diagnostics, add DB/S3 connectivity checks here.
    """
    return {
        "status": "ok",
        "app": getattr(settings, "APP_NAME", "Creative Automation POC"),
        "version": getattr(settings, "APP_VERSION", "0.1.0"),
    }

# info endpoint
@app.get("/", tags=["system"])
async def root() -> dict:
    """
    Simple root endpoint that documents the high-level purpose of the service.
    """
    return {
        "message": "GenAI Creative Automation API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": [
            "/campaigns",
            "/campaigns/{campaign_id}/generate",
            "/assets/{asset_id}",
            "/workflows/{workflow_run_id}",
            "/brands/{brand_id}",
        ],
    }
