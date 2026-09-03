"""
SatQuery AI — Integration Test: End-to-End Mock Flow

Tests the complete pipeline from upload through analysis to final response
without any external API calls.
"""

import io
import os
import pytest
import pytest_asyncio

os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_integration.db")
os.environ.setdefault("UPLOAD_DIR", "./data/uploads")
os.environ.setdefault("RESULTS_DIR", "./data/results")
os.environ.setdefault("CACHE_DIR", "./data/cache")

from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestEndToEndMockFlow:
    """
    Integration tests validating the full demo workflow:
      Upload → Router → Mock Specialist → Evidence → Confidence → Response
    """

    @pytest.mark.asyncio
    async def test_single_image_scene_description_flow(self, client):
        """Demo Flow 1: Single optical image + scene description query."""
        png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 120

        # Upload
        up = await client.post("/api/v1/upload", files={"files": ("scene.png", io.BytesIO(png), "image/png")})
        assert up.status_code == 200
        ud = up.json()

        # Analyze
        resp = await client.post("/api/v1/analyze", json={
            "session_id": ud["session_id"],
            "upload_id": ud["upload_id"],
            "file_ids": [ud["files"][0]["file_id"]],
            "query": "Describe the land cover and major objects visible in this image.",
        })
        assert resp.status_code == 200
        data = resp.json()

        # Validate response contract
        assert data["status"] in ("success", "insufficient_evidence")
        assert data["answer"]["text"]
        assert data["intent"]["type"] in (
            "SCENE_DESCRIPTION", "OBJECT_IDENTIFICATION", "VQA", "UNKNOWN"
        )
        assert data["confidence"]["final_score"] >= 0.0
        assert data["confidence"]["label"] in ("high", "medium", "low", "insufficient")
        assert isinstance(data["execution_trace"], list)
        assert len(data["execution_trace"]) >= 5
        assert isinstance(data["evidence"], list)

    @pytest.mark.asyncio
    async def test_health_and_system_ready(self, client):
        """System must be healthy before running demo."""
        resp = await client.get("/health")
        data = resp.json()
        assert data["status"] == "ok"
        assert data["demo_mode"] is True
        assert data["vision_provider"] == "mock"
        assert data["llm_provider"] == "mock"

    @pytest.mark.asyncio
    async def test_trace_contains_all_expected_steps(self, client):
        """Execution trace must include all pipeline stages."""
        png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 120
        up = await client.post("/api/v1/upload", files={"files": ("img.png", io.BytesIO(png), "image/png")})
        ud = up.json()

        resp = await client.post("/api/v1/analyze", json={
            "session_id": ud["session_id"],
            "upload_id": ud["upload_id"],
            "file_ids": [ud["files"][0]["file_id"]],
            "query": "What can you see in this satellite image?",
        })
        data = resp.json()
        actions = [step["action"] for step in data["execution_trace"]]

        # All major pipeline stages must appear
        assert any("file" in a.lower() or "resolve" in a.lower() for a in actions)
        assert any("config" in a.lower() or "classify" in a.lower() for a in actions)
        assert any("intent" in a.lower() for a in actions)
        assert any("specialist" in a.lower() or "execute" in a.lower() for a in actions)
        assert any("confidence" in a.lower() for a in actions)

    @pytest.mark.asyncio
    async def test_water_query_returns_water_evidence(self, client):
        """Water-focused query should produce water-related evidence."""
        png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 120
        up = await client.post("/api/v1/upload", files={"files": ("water.png", io.BytesIO(png), "image/png")})
        ud = up.json()

        resp = await client.post("/api/v1/analyze", json={
            "session_id": ud["session_id"],
            "upload_id": ud["upload_id"],
            "file_ids": [ud["files"][0]["file_id"]],
            "query": "Identify all water bodies and their extent.",
        })
        data = resp.json()
        assert data["status"] in ("success", "insufficient_evidence")
        # Evidence should mention water in at least one claim
        if data["evidence"]:
            claims = [e["claim"].lower() for e in data["evidence"]]
            assert any("water" in c for c in claims)
