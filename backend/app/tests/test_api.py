"""
SatQuery AI — Backend Tests: API

Tests for all HTTP endpoints: health, upload, analysis.
Uses httpx AsyncClient + pytest-asyncio.
"""

import io
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set minimal env before importing app
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_satquery.db")
os.environ.setdefault("UPLOAD_DIR", "./data/uploads")
os.environ.setdefault("RESULTS_DIR", "./data/results")
os.environ.setdefault("CACHE_DIR", "./data/cache")

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---- Health Endpoint -----------------------------------------------------

class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_contains_required_fields(self, client):
        response = await client.get("/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "demo_mode" in data
        assert data["demo_mode"] is True

    @pytest.mark.asyncio
    async def test_health_app_name(self, client):
        response = await client.get("/health")
        data = response.json()
        assert "SatQuery" in data.get("app_name", "")


# ---- Upload Endpoint -----------------------------------------------------

class TestUploadEndpoint:
    @pytest.mark.asyncio
    async def test_upload_valid_png(self, client):
        # Create minimal PNG bytes (1x1 white pixel)
        png_bytes = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
            b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        response = await client.post(
            "/api/v1/upload",
            files={"files": ("test.png", io.BytesIO(png_bytes), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "upload_id" in data
        assert "session_id" in data
        assert len(data["files"]) == 1
        assert data["files"][0]["extension"] == ".png"

    @pytest.mark.asyncio
    async def test_upload_invalid_extension_rejected(self, client):
        response = await client.post(
            "/api/v1/upload",
            files={"files": ("evil.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "INVALID_FILE_FORMAT"

    @pytest.mark.asyncio
    async def test_upload_returns_session_id(self, client):
        png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        response = await client.post(
            "/api/v1/upload",
            files={"files": ("test.png", io.BytesIO(png_bytes), "image/png")},
        )
        data = response.json()
        assert data.get("session_id")
        assert len(data["session_id"]) > 0

    @pytest.mark.asyncio
    async def test_upload_multiple_files(self, client):
        png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        response = await client.post(
            "/api/v1/upload",
            files=[
                ("files", ("a.png", io.BytesIO(png_bytes), "image/png")),
                ("files", ("b.png", io.BytesIO(png_bytes), "image/png")),
            ],
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) == 2


# ---- Analysis Endpoint --------------------------------------------------

class TestAnalysisEndpoint:
    @pytest.mark.asyncio
    async def test_full_mock_analysis_flow(self, client):
        """End-to-end: upload → analyze → structured response."""
        # Step 1: Upload
        png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        upload_resp = await client.post(
            "/api/v1/upload",
            files={"files": ("scene.png", io.BytesIO(png_bytes), "image/png")},
        )
        assert upload_resp.status_code == 200
        upload_data = upload_resp.json()
        session_id = upload_data["session_id"]
        file_id = upload_data["files"][0]["file_id"]
        upload_id = upload_data["upload_id"]

        # Step 2: Analyze
        analysis_resp = await client.post(
            "/api/v1/analyze",
            json={
                "session_id": session_id,
                "upload_id": upload_id,
                "file_ids": [file_id],
                "query": "Describe what you see in this image.",
            },
        )
        assert analysis_resp.status_code == 200
        data = analysis_resp.json()

        # Verify response contract
        assert "request_id" in data
        assert "status" in data
        assert "answer" in data
        assert "confidence" in data
        assert "execution_trace" in data
        assert "evidence" in data
        assert "disagreement" in data

        # Verify answer has text
        assert data["answer"]["text"]

        # Verify execution trace has steps
        assert len(data["execution_trace"]) > 0

        # Verify confidence has score
        assert "final_score" in data["confidence"]
        assert 0.0 <= data["confidence"]["final_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_analysis_invalid_session_returns_error(self, client):
        response = await client.post(
            "/api/v1/analyze",
            json={
                "session_id": "nonexistent-session",
                "upload_id": "fake",
                "file_ids": ["nonexistent-file-id"],
                "query": "Describe this image.",
            },
        )
        # Should return an error — file not found
        assert response.status_code in (404, 422, 500)

    @pytest.mark.asyncio
    async def test_analysis_empty_query_rejected(self, client):
        response = await client.post(
            "/api/v1/analyze",
            json={
                "session_id": "s",
                "upload_id": "u",
                "file_ids": ["f"],
                "query": "",  # Empty query — should fail validation
            },
        )
        assert response.status_code == 422


# ---- Error Response Format ----------------------------------------------

class TestErrorFormat:
    @pytest.mark.asyncio
    async def test_error_response_has_correct_structure(self, client):
        response = await client.post(
            "/api/v1/upload",
            files={"files": ("bad.xyz", io.BytesIO(b"content"), "text/plain")},
        )
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        # Ensure no stack trace leaked
        assert "traceback" not in str(data).lower()
        assert "exception" not in str(data).lower()
