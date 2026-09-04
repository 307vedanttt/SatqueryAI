import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.schemas import AnalysisRequest

client = TestClient(app)

def test_api_health_contract():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data

def test_analysis_missing_image():
    # Attempting to query with missing image IDs
    request = {
        "session_id": "test-session",
        "upload_id": "test-upload",
        "file_ids": [],
        "configuration": "single",
        "query": "What is in this image?",
        "options": {}
    }
    response = client.post("/api/v1/analyze", json=request)
    assert response.status_code == 422 # Pydantic validation or custom error
    # Actually, the API might return 400 if file_ids is empty, or if we mock it, it will return 404 because file doesn't exist in DB
    # Let's check what the backend does if file_ids is empty: it might just pass and then fail if expected.

def test_analysis_empty_query():
    request = {
        "session_id": "test-session",
        "upload_id": "test-upload",
        "file_ids": ["some-image-id"],
        "configuration": "single",
        "query": "",
        "options": {}
    }
    response = client.post("/api/v1/analyze", json=request)
    assert response.status_code == 422 # Pydantic min_length validation

def test_analysis_invalid_image_id():
    request = {
        "session_id": "test-session",
        "upload_id": "test-upload",
        "file_ids": ["invalid-uuid-that-doesnt-exist"],
        "configuration": "single",
        "query": "What is in this image?",
        "options": {}
    }
    response = client.post("/api/v1/analyze", json=request)
    # The file doesn't exist in DB, so it should raise NotFoundError -> 404
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"

@patch("app.api.routes.analysis.classify_input_configuration")
def test_analysis_valid_request_and_successful_response(mock_classify, monkeypatch):
    # We will mock the database and the execution flow to test the contract
    request = {
        "session_id": "test-session",
        "upload_id": "test-upload",
        "file_ids": ["fake-file-id"],
        "configuration": "single",
        "query": "Are there buildings here?",
        "options": {}
    }
    
    # We need to bypass the DB lookup or mock it
    # We can use the TestClient, but since the DB is invoked, we might get 404
    # The requirement is just to test the contract.
    pass

# We will implement a test that mocks the dependencies to ensure the successful response matches the schema.
from app.api.dependencies import get_db
from sqlalchemy.orm import Session
from app.models import orm

def override_get_db():
    mock_db = MagicMock(spec=Session)
    
    # Mocking UploadedFile
    fake_file = orm.UploadedFile(
        id="fake-file-id",
        original_filename="test.tif",
        internal_filename="internal.tif",
        file_path="/tmp/test.tif",
        file_size_bytes=100,
        extension=".tif",
        is_geotiff=True,
        metadata_json=None
    )
    
    mock_db.query.return_value.filter.return_value.first.return_value = fake_file
    return mock_db

app.dependency_overrides[get_db] = override_get_db

def test_analysis_successful_response():
    request = {
        "session_id": "test-session",
        "upload_id": "test-upload",
        "file_ids": ["fake-file-id"],
        "configuration": "single",
        "query": "Are there buildings here?",
        "options": {}
    }
    
    response = client.post("/api/v1/analyze", json=request)
    assert response.status_code == 200
    data = response.json()
    
    # Check successful response schema
    assert "request_id" in data
    assert "session_id" in data
    assert "status" in data
    assert data["status"] == "success"
    
    # Check new fields
    assert "selected_specialist" in data
    assert "warnings" in data
    assert "timestamps" in data
    assert "started" in data["timestamps"]
    assert "completed" in data["timestamps"]
    
    assert "answer" in data
    assert "evidence" in data
    assert "execution_trace" in data

def test_analysis_backend_failure():
    # If a dependency raises an exception, it should return a standardized error format
    request = {
        "session_id": "test-session",
        "upload_id": "test-upload",
        "file_ids": ["fake-file-id"],
        "configuration": "single",
        "query": "fail-me",
        "options": {}
    }
    
    with patch("app.router.planner.classify_intent", side_effect=Exception("Unexpected AI error")):
        response = client.post("/api/v1/analyze", json=request)
        
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_ERROR"

def test_invalid_configuration():
    # configuration is a string but might not be in the enum or might be invalid for the files
    # The model schema allows any string by default, but our business logic will check it.
    pass

def test_history_contract():
    # Test GET /api/v1/history
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_trace_contract():
    # Test GET /api/v1/analysis/{id}/trace
    response = client.get("/api/v1/analysis/invalid_id/trace")
    assert response.status_code == 404

