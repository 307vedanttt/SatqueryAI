"""
schemas/contracts.py — Shared Pydantic contracts for SatQuery AI

This is the SINGLE SOURCE OF TRUTH for inter-module data shapes.
Every teammate's module (agent, models/vqa, models/change, models/fusion,
remote_sensing, frontend API) imports from here and returns/accepts EXACTLY
these types. Do not modify field names or types without a team-wide discussion
— changing these shapes breaks integration for everyone.

Persons A, B, C, D, E all import from this file. It is intentionally kept
minimal and free of business logic.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================
# ImageMetadata — describes a single uploaded image file
# ============================================================

class ImageMetadata(BaseModel):
    """
    Metadata for a single input image.

    All fields except file_path are optional because benchmark images
    (PNG/JPEG from VRSBench, RSVQA, etc.) lack geospatial metadata.
    Modules that require specific fields (e.g., CRS for co-registration)
    must validate them explicitly rather than assuming they are set.
    """

    sensor: str = Field(
        ...,
        description="Sensor modality: 'optical', 'sar', or 'multispectral'",
        examples=["optical", "sar"],
    )
    crs: Optional[str] = Field(
        default=None,
        description="Coordinate Reference System string (e.g. 'EPSG:4326'). "
                    "None for benchmark images without geospatial reference.",
    )
    width: int = Field(default=0, ge=0, description="Image width in pixels")
    height: int = Field(default=0, ge=0, description="Image height in pixels")
    bands: int = Field(default=1, ge=1, description="Number of spectral bands")
    resolution_m: float = Field(
        default=0.0, ge=0.0,
        description="Ground sampling distance in metres per pixel. "
                    "0.0 for benchmark images without geospatial metadata.",
    )
    acquisition_date: Optional[str] = Field(
        default=None,
        description="ISO-8601 date string (YYYY-MM-DD) or None if unknown",
    )
    file_path: str = Field(
        ...,
        description="Absolute or relative path to the image file on disk",
    )


# ============================================================
# SpecialistRequest — input to any specialist model callable
# ============================================================

class SpecialistRequest(BaseModel):
    """
    Standardised input contract for all specialist callables.

    The agent/executor.py constructs this and passes it to whichever
    tool the router selected. All specialist functions (run_vqa,
    run_captioning, run_grounding, run_change_detection,
    run_optical_sar_fusion) accept exactly this type.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's original natural-language question",
    )
    images: list[ImageMetadata] = Field(
        ...,
        description="Ordered list of images for this request. "
                    "Single-image tools expect len==1; multi-image tools expect len==2.",
    )
    task_hint: str = Field(
        default="",
        description="Tool name as classified by the router (e.g. 'change_vqa'). "
                    "Specialist implementations may use this to adjust behaviour.",
    )


# ============================================================
# BoundingBox — normalised image-space coordinates
# ============================================================

class BoundingBox(BaseModel):
    """
    Axis-aligned bounding box in image pixel or normalised (0–1000) coordinates.

    IMPORTANT: These are IMAGE-SPACE coordinates, NOT geographic lat/lon.
    They describe a rectangular region within the pixel grid of the input image.
    Do not conflate them with real-world geographic extents.

    Coordinate convention matches Qwen2.5-VL output:
        (x1, y1) = top-left corner
        (x2, y2) = bottom-right corner
    Values may be raw pixels or normalised 0–1000 depending on model output;
    the grounding module documents which convention it returns.
    """

    x1: int = Field(..., ge=0, description="Left edge (pixels or normalised 0-1000)")
    y1: int = Field(..., ge=0, description="Top edge (pixels or normalised 0-1000)")
    x2: int = Field(..., ge=0, description="Right edge (pixels or normalised 0-1000)")
    y2: int = Field(..., ge=0, description="Bottom edge (pixels or normalised 0-1000)")
    label: str = Field(
        default="",
        description="Human-readable label for what is enclosed by this box",
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Model confidence for this specific box (0.0–1.0)",
    )


# ============================================================
# SpecialistResponse — output from any specialist model callable
# ============================================================

class SpecialistResponse(BaseModel):
    """
    Standardised output contract for all specialist callables.

    Every specialist function must return exactly this shape.
    The agent/executor.py relies on status, confidence_tier, and error_message
    to decide retry/abort logic without inspecting tool-specific internals.
    """

    task: str = Field(
        ...,
        description="Task type performed, matching the tool name: "
                    "'vqa', 'captioning', 'grounding', 'change_detection', "
                    "'change_vqa', 'optical_sar_fusion'",
    )
    answer: str = Field(
        ...,
        description="The model-generated natural-language answer. "
                    "Must be a genuine generated string, never a hard-coded fabrication.",
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Raw numeric confidence score from the model (0.0–1.0). "
                    "May be 0.0 if the model does not produce a confidence score.",
    )
    confidence_tier: str = Field(
        ...,
        description="Human-readable confidence category: 'high', 'moderate', or 'insufficient'",
        pattern="^(high|moderate|insufficient)$",
    )
    bounding_boxes: list[BoundingBox] = Field(
        default_factory=list,
        description="Bounding boxes returned by grounding tasks. "
                    "Empty list for non-grounding tasks.",
    )
    evidence: str = Field(
        default="",
        description="Short human-readable description of how the answer was derived "
                    "(e.g. 'Generated from full-image analysis'). Used in execution trace.",
    )
    model_used: str = Field(
        default="",
        description="Identifier of the model/pipeline that produced this response "
                    "(e.g. 'Qwen2.5-VL-3B-Instruct'). Used for auditability.",
    )
    status: str = Field(
        ...,
        description="Execution outcome: 'success' or 'error'",
        pattern="^(success|error)$",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Human-readable error description when status='error'. "
                    "Must be set on error; must be None on success.",
    )


# ============================================================
# ExecutionStep — a single recorded step in the execution trace
# ============================================================

class ExecutionStep(BaseModel):
    """
    One auditable step in the agent's execution trace.

    Every major action the executor takes (input validation, routing,
    precondition check, tool execution, retry) must be appended to the
    trace as an ExecutionStep so the full reasoning chain is visible.
    This directly implements the problem statement's
    "auditable execution summary" requirement.
    """

    step_number: int = Field(..., ge=1, description="1-indexed step counter")
    action: str = Field(
        ...,
        description="Human-readable description of what this step did "
                    "(e.g. 'Validated input metadata', 'Classified intent -> change_vqa')",
    )
    tool_used: Optional[str] = Field(
        default=None,
        description="Name of the tool invoked in this step, if any (e.g. 'change_vqa'). "
                    "None for non-tool steps like validation or routing.",
    )
    result_summary: str = Field(
        ...,
        description="Brief outcome description for display in the trace "
                    "(e.g. '2 images validated, CRS match confirmed', 'success', 'failed: OOM')",
    )


# ============================================================
# ExecutionTrace — the complete reasoning chain for one request
# ============================================================

class ExecutionTrace(BaseModel):
    """
    Complete, ordered record of the agent's reasoning for one analysis request.

    Returned alongside every SpecialistResponse so the UI can render a
    step-by-step explanation of how the answer was produced. This is the
    primary evidence that the system is deterministic and auditable,
    which is the most heavily graded requirement in SIH26167.
    """

    query: str = Field(..., description="The original user query")
    intent_classified: str = Field(
        ...,
        description="Tool name selected by the router (e.g. 'change_vqa')",
    )
    steps: list[ExecutionStep] = Field(
        default_factory=list,
        description="Ordered list of all execution steps, including failures and retries",
    )
    final_confidence_tier: str = Field(
        ...,
        description="Confidence tier of the final response: 'high', 'moderate', or 'insufficient'",
        pattern="^(high|moderate|insufficient)$",
    )
    total_steps: int = Field(
        ..., ge=0,
        description="Total number of steps executed (matches len(steps))",
    )
