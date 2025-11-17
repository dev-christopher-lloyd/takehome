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
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
  # Configure structured logging once at startup
  core_logging.configure_logging()

  yield


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

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
  return JSONResponse(
      status_code=500,
      content={
          "detail": "Internal server error",
          "error_type": exc.__class__.__name__,
      },
  )


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


@app.get("/healthz", tags=["system"])
async def healthcheck() -> dict:
  return {
      "status": "up",
      "app": getattr(settings, "APP_NAME", "Creative Automation POC"),
      "version": getattr(settings, "APP_VERSION", "0.1.0"),
  }
