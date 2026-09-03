# SatQuery AI — API Contract Specification

All API endpoints reside under `/api/v1` except health.

## 1. GET `/health`
Returns system status and provider configuration.

## 2. POST `/api/v1/upload`
Form-data upload supporting multiple files (`files`).
Returns `UploadResponse` containing UUID-based internal file IDs and GeoTIFF metadata.

## 3. POST `/api/v1/analyze`
Executes the orchestration graph.
Request: `AnalysisRequest` (`session_id`, `upload_id`, `file_ids`, `query`).
Response: `AnalysisResponse` containing answer, confidence breakdown, evidence list, disagreement flags, and execution trace.

## 4. GET `/api/v1/analysis/{request_id}`
Retrieves a previously completed analysis result.
