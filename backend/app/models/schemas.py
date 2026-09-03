"""
SatQuery AI — Pydantic API Schemas

These are the CONTRACTS between frontend and backend.
All request/response bodies are typed via these models.
The frontend TypeScript types mirror these exactly.

RULE: Never pass raw dicts across service boundaries.
      Always use typed models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Enumerations
# ============================================================

class InputConfiguration(str, Enum):
    SINGLE_OPTICAL = "SINGLE_OPTICAL"
    SINGLE_SAR = "SINGLE_SAR"
    OPTICAL_SAR_PAIR = "OPTICAL_SAR_PAIR"
    BI_TEMPORAL = "BI_TEMPORAL"
    UNKNOWN = "UNKNOWN"


class QueryIntent(str, Enum):
    SCENE_DESCRIPTION = "SCENE_DESCRIPTION"
    VQA = "VQA"
    GROUNDING = "GROUNDING"
    CHANGE_DESCRIPTION = "CHANGE_DESCRIPTION"
    CHANGE_VQA = "CHANGE_VQA"
    OPTICAL_SAR_ANALYSIS = "OPTICAL_SAR_ANALYSIS"
    BUILT_UP_ANALYSIS = "BUILT_UP_ANALYSIS"
    WATER_ANALYSIS = "WATER_ANALYSIS"
    OBJECT_IDENTIFICATION = "OBJECT_IDENTIFICATION"
    UNKNOWN = "UNKNOWN"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceType(str, Enum):
    REGION = "region"
    BBOX = "bbox"
    MASK = "mask"
    PIXEL_AREA = "pixel_area"
    METADATA = "metadata"
    TEMPORAL_DIFFERENCE = "temporal_difference"
    SENSOR_COMPARISON = "sensor_comparison"
    MODEL_PREDICTION = "model_prediction"


class ConfidenceLabel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


class ExecutionStepStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


# ============================================================
# Image Metadata
# ============================================================

class ImageMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    image_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    filename: str
    width: int | None = None
    height: int | None = None
    bands: int | None = None
    dtype: str | None = None
    crs: str | None = None
    resolution: tuple[float, float] | None = None
    bounds: tuple[float, float, float, float] | None = None
    nodata: float | None = None
    driver: str | None = None
    is_geotiff: bool = False
    sensor: str | None = None
    acquisition_date: str | None = None
    image_type: str | None = None  # "optical" | "sar" | "multispectral" | "unknown"
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# Upload
# ============================================================

class UploadedFileInfo(BaseModel):
    file_id: str
    original_filename: str
    internal_filename: str
    size_bytes: int
    extension: str
    is_geotiff: bool
    metadata: ImageMetadata | None = None


class UploadResponse(BaseModel):
    upload_id: str
    session_id: str
    files: list[UploadedFileInfo]
    message: str = "Files uploaded successfully."


# ============================================================
# Analysis Request
# ============================================================

class AnalysisRequest(BaseModel):
    session_id: str
    upload_id: str
    file_ids: list[str]
    query: str = Field(min_length=1, max_length=2000)


# ============================================================
# Intent / Route Plan
# ============================================================

class IntentResult(BaseModel):
    type: QueryIntent
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str | None = None
    required_capabilities: list[str] = Field(default_factory=list)


class RoutePlan(BaseModel):
    input_configuration: InputConfiguration
    intent: IntentResult
    execution_steps: list[str]  # ordered list of tool/step names
    specialist: str


# ============================================================
# Specialist
# ============================================================

class SpecialistRequest(BaseModel):
    request_id: str
    specialist_name: str
    input_configuration: InputConfiguration
    intent: QueryIntent
    file_ids: list[str]
    file_paths: list[str]
    metadata: list[ImageMetadata]
    query: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    evidence_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    specialist: str
    source: str
    claim: str
    evidence_type: EvidenceType = EvidenceType.MODEL_PREDICTION
    region: dict[str, Any] | None = None
    bbox: list[int] | None = None          # [x1, y1, x2, y2]
    date: str | None = None
    sensor: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SpecialistResult(BaseModel):
    specialist: str
    status: AnalysisStatus
    answer: str
    evidence: list[Evidence] = Field(default_factory=list)
    raw_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# Confidence
# ============================================================

class ConfidenceBreakdown(BaseModel):
    input_score: float = Field(ge=0.0, le=1.0)
    specialist_score: float = Field(ge=0.0, le=1.0)
    evidence_score: float = Field(ge=0.0, le=1.0)
    agreement_score: float = Field(ge=0.0, le=1.0)
    final_score: float = Field(ge=0.0, le=1.0)
    label: ConfidenceLabel
    explanation: str


# ============================================================
# Disagreement
# ============================================================

class DisagreementItem(BaseModel):
    source: str
    claim: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class DisagreementResult(BaseModel):
    detected: bool
    items: list[DisagreementItem] = Field(default_factory=list)
    explanation: str | None = None


# ============================================================
# Execution Trace
# ============================================================

class ExecutionStep(BaseModel):
    step_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    step_index: int
    timestamp: datetime
    action: str
    component: str
    status: ExecutionStepStatus
    duration_ms: int | None = None
    output_summary: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# Analysis Response (full contract)
# ============================================================

class AnswerBlock(BaseModel):
    text: str
    is_refused: bool = False
    refusal_reason: str | None = None


class AnalysisResponse(BaseModel):
    request_id: str
    session_id: str
    status: AnalysisStatus

    input: dict[str, Any]          # configuration + file list

    intent: IntentResult | None = None

    answer: AnswerBlock

    evidence: list[Evidence] = Field(default_factory=list)

    confidence: ConfidenceBreakdown | None = None

    disagreement: DisagreementResult = Field(
        default_factory=lambda: DisagreementResult(detected=False)
    )

    execution_trace: list[ExecutionStep] = Field(default_factory=list)

    visual_outputs: list[dict[str, Any]] = Field(default_factory=list)

    created_at: datetime | None = None
    duration_ms: int | None = None


# ============================================================
# Error Response
# ============================================================

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ============================================================
# Session
# ============================================================

class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    analysis_count: int
    upload_count: int
