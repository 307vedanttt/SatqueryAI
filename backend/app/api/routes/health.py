"""SatQuery AI — GET /health"""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.database import check_db_connection

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    app_name: str
    demo_mode: bool
    database: str
    timestamp: str
    vision_provider: str
    llm_provider: str


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """
    Returns current system health status.
    Safe to call without authentication.
    """
    settings = get_settings()
    db_ok = check_db_connection()

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        version=settings.APP_VERSION,
        app_name=settings.APP_NAME,
        demo_mode=settings.DEMO_MODE,
        database="connected" if db_ok else "disconnected",
        timestamp=datetime.now(timezone.utc).isoformat(),
        vision_provider=settings.effective_vision_provider,
        llm_provider=settings.effective_llm_provider,
    )
