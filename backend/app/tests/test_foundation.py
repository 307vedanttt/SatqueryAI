import os
import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.main import app, create_app
from app.core.config import Settings

@pytest.fixture
def client():
    # Provide a sync fixture for async client initialization
    import asyncio
    loop = asyncio.get_event_loop()
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")
        assert "version" in data
        assert "app_name" in data

@pytest.mark.asyncio
async def test_health_endpoint_trailing_slash():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")

@pytest.mark.asyncio
async def test_readiness_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ready", "not_ready")
        assert data["database"] in ("ok", "error")

def test_application_startup():
    """Test that the application can be instantiated without errors."""
    test_app = create_app()
    assert test_app is not None
    assert test_app.title == "SatQuery AI"

def test_configuration_loading():
    """Test that settings load correctly from defaults or env."""
    settings = Settings(APP_NAME="Test App", DEMO_MODE=True)
    assert settings.APP_NAME == "Test App"
    assert settings.DEMO_MODE is True
    assert settings.max_upload_bytes > 0

def test_invalid_configuration():
    """Test that Pydantic rejects invalid configuration values."""
    with pytest.raises(ValidationError):
        # CONFIDENCE_WEIGHT_INPUT must be between 0.0 and 1.0
        Settings(CONFIDENCE_WEIGHT_INPUT=1.5)

@pytest.mark.asyncio
async def test_api_error_handling():
    """Test that unexpected routes or bad data return proper JSON formats, no stack traces."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Generate a 404
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404
        data = response.json()
        # FastAPI's default 404 is {"detail": "Not Found"}
        assert "detail" in data

        # Test global SatQuery error format by triggering validation error on upload
        response = await client.post("/api/v1/upload", files={})
        assert response.status_code == 422
        # Pydantic validation error returns 422 with {"detail": ...}
        # But if we throw SatQueryError or Exception, our custom handlers catch it.
        # Check custom 422 error structure.
        data = response.json()
        assert "detail" in data or "error" in data
