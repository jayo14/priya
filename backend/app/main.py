"""Priya FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import (
    dashboard,
    health,
    promotions,
    providers,
    settings as settings_route,
    sources,
    watchlist,
)
from app.core.config import settings
from app.core.logging import setup_logging

logger = setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown."""
    logger.info(
        f"Starting {settings.APP_NAME} backend in '{settings.APP_ENV}' mode (debug={settings.DEBUG})"
    )
    yield
    logger.info(f"Shutting down {settings.APP_NAME} backend")


app = FastAPI(
    title=settings.APP_NAME,
    description="Deterministic AI Subscription Promotion Discovery Engine Backend",
    version="0.1.0",
    docs_url=f"{settings.API_PREFIX}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_PREFIX}/redoc" if settings.DEBUG else None,
    openapi_url=f"{settings.API_PREFIX}/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Safely handle database errors without leaking connection details or queries."""
    logger.error(f"Database error occurred during {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred while processing the request."},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Safely catch unhandled application exceptions."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred."},
    )


# Register API routers
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(sources.router, prefix=settings.API_PREFIX)
app.include_router(promotions.router, prefix=settings.API_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(providers.router, prefix=settings.API_PREFIX)
app.include_router(watchlist.router, prefix=settings.API_PREFIX)
app.include_router(settings_route.router, prefix=settings.API_PREFIX)


@app.get("/", include_in_schema=False)
def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "api_docs": f"{settings.API_PREFIX}/docs" if settings.DEBUG else "disabled",
    }
