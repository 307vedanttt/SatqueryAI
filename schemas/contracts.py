"""
SatQuery AI — Shared Contract Schemas (SIH26167)

This module defines the shared Pydantic models required across all SIH26167 modules:
- ImageMetadata
- BoundingBox
- SpecialistRequest
- SpecialistResponse
- ExecutionStep
- ExecutionTrace

Do not alter field names or types as all team modules depend on this exact contract.
"""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class ImageMetadata(BaseModel):
    sensor: str = Field(default="optical", description="Sensor type: 'optical', 'sar', or 'multispectral'")
    crs: str = Field(default="EPSG:4326", description="Coordinate Reference System string or 'none'")
    width: int = Field(default=1024, ge=0)
    height: int = Field(default=1024, ge=0)
    bands: int = Field(default=3, ge=1)
    resolution_m: float = Field(default=10.0, ge=0.0, description="Spatial resolution in meters")
    acquisition_date: Optional[str] = Field(default=None, description="ISO acquisition date string")
    file_path: str = Field(description="Absolute path to the image file")


class BoundingBox(BaseModel):
    label: str = Field(description="Target object or region label")
    xmin: float = Field(description="Normalized (0-1000 or 0-1) or pixel coordinate")
    ymin: float = Field(description="Normalized (0-1000 or 0-1) or pixel coordinate")
    xmax: float = Field(description="Normalized (0-1000 or 0-1) or pixel coordinate")
    ymax: float = Field(description="Normalized (0-1000 or 0-1) or pixel coordinate")


class SpecialistRequest(BaseModel):
    query: str = Field(description="User natural-language query")
    images: list[ImageMetadata] = Field(description="List of uploaded image metadata objects")
    task_hint: Optional[str] = Field(default=None, description="Optional task classification hint")


class SpecialistResponse(BaseModel):
    task: str = Field(description="Name of the task executed")
    answer: str = Field(description="Generated natural language response")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    confidence_tier: Literal["high", "moderate", "low", "insufficient"] = Field(default="moderate")
    bounding_boxes: list[BoundingBox] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    model_used: str = Field(default="STUB-Specialist")
    status: Literal["success", "error"] = Field(default="success")
    error_message: Optional[str] = Field(default=None)


class ExecutionStep(BaseModel):
    step_number: int
    action: str
    tool_used: str
    result_summary: str


class ExecutionTrace(BaseModel):
    query: str
    intent_classified: str
    steps: list[ExecutionStep] = Field(default_factory=list)
    final_confidence_tier: Literal["high", "moderate", "low", "insufficient"] = Field(default="moderate")
    total_steps: int
