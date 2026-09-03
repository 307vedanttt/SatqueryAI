"""
SatQuery AI — FastAPI Dependencies

Provides injectable dependencies for:
- Database session
- Application settings
- Registry access
"""

from typing import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.database import get_db
from app.registry.registry import SpecialistRegistry


def get_registry(request: Request) -> SpecialistRegistry:
    """Retrieve the shared registry from app state."""
    return request.app.state.registry


# Re-export for use with Depends()
__all__ = ["get_db", "get_settings", "get_registry"]
