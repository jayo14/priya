"""Health check endpoint distinguishing application and database readiness."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.database.session import check_database_connection

router = APIRouter(tags=["Health"])


class DatabaseHealth(BaseModel):
    connected: bool
    status: str
    latency_ms: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    timestamp_utc: str
    timezone: str
    database: DatabaseHealth


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application and database health check",
    description="Returns service availability and checks database connectivity without exposing sensitive credentials.",
)
def get_health(settings: Settings = Depends(get_settings)) -> JSONResponse:
    is_db_connected, latency_ms, db_status_msg = check_database_connection()

    app_status = "healthy" if is_db_connected else "degraded"
    http_status = status.HTTP_200_OK if is_db_connected else status.HTTP_503_SERVICE_UNAVAILABLE

    payload = {
        "status": app_status,
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "timezone": settings.TIMEZONE,
        "database": {
            "connected": is_db_connected,
            "status": "connected" if is_db_connected else "unavailable",
            "latency_ms": latency_ms,
        },
    }

    return JSONResponse(status_code=http_status, content=payload)
