"""
SatQuery AI — Single-Image Grounding Specialist

Localizes regions or objects in a single remote-sensing image based on
a natural-language query using the project's VisionProvider abstraction.

Key rules:
  - Accepts exactly one image.
  - Accepts a query describing an object or region.
  - Asks the selected vision model/provider to localize the requested object.
  - Parses the model's documented coordinate format.
  - Converts output into the existing BoundingBox contract: [x1, y1, x2, y2]
    as non-negative integers in IMAGE PIXEL SPACE (not geographic lat/lon).
  - Validates coordinate integrity (x1 < x2, y1 < y2, non-negative, inside image).
  - Never fabricates a bounding box.
  - Returns explicit error/failed result when coordinates are missing or malformed.
"""

from __future__ import annotations

import asyncio
import json
import math
import re
import uuid
from typing import Any

from app.core.logging import get_logger
from app.models.schemas import (
    AnalysisStatus,
    Evidence,
    EvidenceType,
    SpecialistRequest,
    SpecialistResult,
)
from app.providers.base import VisionProvider
from app.registry.capabilities import Capability
from app.specialists.base import Specialist

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Coordinate Parsing & Validation
# ---------------------------------------------------------------------------

def parse_bounding_box(
    raw_box: Any,
    image_width: int | None = None,
    image_height: int | None = None,
    coordinate_format: str | None = None,
) -> tuple[list[int] | None, str | None]:
    """
    Parse and validate raw model bounding box output into standard
    image-space integer pixel coordinates [x1, y1, x2, y2].

    Supported input formats:
      - list/tuple of 4 numbers: [x1, y1, x2, y2]
      - Gemini box_2d: [ymin, xmin, ymax, xmax] in 0..1000 scale
      - normalized float: [x1, y1, x2, y2] in 0.0..1.0 scale (requires dimensions)
      - dict: {"x1": ..., "y1": ..., "x2": ..., "y2": ...}
      - dict: {"xmin": ..., "ymin": ..., "xmax": ..., "ymax": ...}
      - dict: {"box_2d": [ymin, xmin, ymax, xmax]}
      - string containing JSON or [n1, n2, n3, n4]

    Returns:
        (bbox, None) on success, where bbox is [x1, y1, x2, y2] with ints.
        (None, error_message) on validation failure.
    """
    if raw_box is None:
        return None, "Bounding box coordinates are missing (None)."

    # 1. Unpack string representations
    if isinstance(raw_box, str):
        raw_box = raw_box.strip()
        try:
            raw_box = json.loads(raw_box)
        except (json.JSONDecodeError, ValueError):
            # Try regex extraction of 4 numbers from string
            match = re.search(
                r"\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]",
                raw_box,
            )
            if match:
                raw_box = [float(match.group(i)) for i in range(1, 5)]
            else:
                return None, f"Cannot parse bounding box string: '{raw_box[:80]}'."

    # 2. Unpack dict representations
    if isinstance(raw_box, dict):
        if "bbox" in raw_box:
            return parse_bounding_box(
                raw_box["bbox"],
                image_width=image_width,
                image_height=image_height,
                coordinate_format=coordinate_format or raw_box.get("format"),
            )
        if "box_2d" in raw_box:
            return parse_bounding_box(
                raw_box["box_2d"],
                image_width=image_width,
                image_height=image_height,
                coordinate_format="box_2d",
            )
        if "box" in raw_box:
            return parse_bounding_box(
                raw_box["box"],
                image_width=image_width,
                image_height=image_height,
                coordinate_format=coordinate_format or raw_box.get("format"),
            )

        if {"x1", "y1", "x2", "y2"}.issubset(raw_box.keys()):
            raw_box = [raw_box["x1"], raw_box["y1"], raw_box["x2"], raw_box["y2"]]
        elif {"xmin", "ymin", "xmax", "ymax"}.issubset(raw_box.keys()):
            raw_box = [raw_box["xmin"], raw_box["ymin"], raw_box["xmax"], raw_box["ymax"]]
        elif {"ymin", "xmin", "ymax", "xmax"}.issubset(raw_box.keys()):
            raw_box = [raw_box["xmin"], raw_box["ymin"], raw_box["xmax"], raw_box["ymax"]]
        else:
            return None, f"Unrecognized bounding box dict keys: {list(raw_box.keys())}."

    # 3. Must be a 4-element sequence
    if not isinstance(raw_box, (list, tuple)):
        return None, f"Bounding box must be a list or tuple of 4 numbers, got {type(raw_box).__name__}."

    if len(raw_box) != 4:
        return None, f"Bounding box must contain exactly 4 coordinates, got {len(raw_box)}."

    # 4. Verify all elements are finite numbers
    coords: list[float] = []
    for idx, v in enumerate(raw_box):
        try:
            val = float(v)
            if math.isnan(val) or math.isinf(val):
                return None, f"Coordinate at index {idx} is not finite: {v}."
            coords.append(val)
        except (TypeError, ValueError):
            return None, f"Coordinate at index {idx} is not numeric: {v!r}."

    # 5. Format conversion to [x1, y1, x2, y2]
    # Check for Gemini box_2d [ymin, xmin, ymax, xmax] in 0..1000
    is_gemini_1000 = coordinate_format in ("box_2d", "ymin_xmin_ymax_xmax_1000")

    if is_gemini_1000:
        ymin, xmin, ymax, xmax = coords
        if image_width is not None and image_height is not None:
            x1 = int(round(xmin * image_width / 1000.0))
            y1 = int(round(ymin * image_height / 1000.0))
            x2 = int(round(xmax * image_width / 1000.0))
            y2 = int(round(ymax * image_height / 1000.0))
        else:
            x1, y1, x2, y2 = int(round(xmin)), int(round(ymin)), int(round(xmax)), int(round(ymax))
    elif coordinate_format in ("normalized", "normalized_0_1"):
        # Normalized float coordinates in 0.0..1.0
        if image_width is None or image_height is None:
            return None, "Normalized 0-1 coordinates require image width and height to convert to image space."
        x1 = int(round(coords[0] * image_width))
        y1 = int(round(coords[1] * image_height))
        x2 = int(round(coords[2] * image_width))
        y2 = int(round(coords[3] * image_height))
    else:
        # Standard pixel coordinates [x1, y1, x2, y2]
        x1 = int(round(coords[0]))
        y1 = int(round(coords[1]))
        x2 = int(round(coords[2]))
        y2 = int(round(coords[3]))

    # 6. Geometric integrity validation
    if x1 < 0 or y1 < 0:
        return None, f"Coordinates cannot be negative: x1={x1}, y1={y1}."

    if x1 >= x2:
        return None, f"Invalid bounding box width: x1 ({x1}) must be strictly less than x2 ({x2})."

    if y1 >= y2:
        return None, f"Invalid bounding box height: y1 ({y1}) must be strictly less than y2 ({y2})."

    # 7. Image boundary validation if dimensions are known
    if image_width is not None and image_height is not None:
        if x1 >= image_width or y1 >= image_height:
            return (
                None,
                f"Bounding box origin ({x1}, {y1}) is outside image boundaries ({image_width}x{image_height}).",
            )
        # Allow minor boundary overshoot (up to 5%) and clamp
        if x2 > image_width * 1.05 or y2 > image_height * 1.05:
            return (
                None,
                f"Bounding box exceeds image dimensions: bottom-right ({x2}, {y2}) exceeds ({image_width}x{image_height}).",
            )
        x2 = min(x2, image_width)
        y2 = min(y2, image_height)

    return [x1, y1, x2, y2], None


# ---------------------------------------------------------------------------
# Grounding Specialist
# ---------------------------------------------------------------------------

class GroundingSpecialist(Specialist):
    """
    Single-image spatial grounding and localization specialist.

    Delegates inference to a VisionProvider to locate objects described
    in the query, rigorously validates bounding box coordinates, and
    returns a typed SpecialistResult.
    """

    def __init__(
        self,
        vision_provider: VisionProvider,
        name: str = "grounding",
    ) -> None:
        self._vision = vision_provider
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> list[str]:
        return [Capability.GROUNDING]

    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        """
        Execute text-guided grounding on exactly one image.
        """
        # ---- 1. Validate: exactly one image --------------------------------
        n_images = len(request.metadata)
        if n_images != 1:
            return SpecialistResult(
                specialist=self.name,
                status=AnalysisStatus.FAILED,
                answer="",
                error=(
                    f"Grounding requires exactly 1 image, but {n_images} "
                    f"{'were' if n_images != 1 else 'was'} provided."
                ),
                raw_confidence=0.0,
                metadata={
                    "task": "grounding",
                    "provider": self._vision.provider_name,
                },
            )

        # ---- 2. Validate: query describing an object/region ----------------
        query = request.query.strip() if request.query else ""
        if not query:
            return SpecialistResult(
                specialist=self.name,
                status=AnalysisStatus.FAILED,
                answer="",
                error="Grounding requires a non-empty query describing the object or region to localize.",
                raw_confidence=0.0,
                metadata={
                    "task": "grounding",
                    "provider": self._vision.provider_name,
                },
            )

        image_path = request.file_paths[0]
        image_meta = request.metadata[0]

        # Construct prompt asking model for identification and localization
        grounding_prompt = (
            f"Identify and localize the region or object corresponding to: '{query}'. "
            "Return the bounding box coordinates in image pixel space as [x1, y1, x2, y2]."
        )

        meta_hints: dict[str, Any] = {
            "filename": image_meta.filename,
            "image_type": image_meta.image_type,
            "crs": image_meta.crs,
            "sensor": image_meta.sensor,
            "task": "grounding",
            "target": query,
            "image_width": image_meta.width,
            "image_height": image_meta.height,
        }

        # ---- 3. Call vision provider ---------------------------------------
        try:
            result = await self._vision.analyze_image(
                image_path=image_path,
                prompt=grounding_prompt,
                metadata=meta_hints,
            )
        except Exception as exc:
            try:
                logger.error(
                    "grounding_provider_error",
                    provider=self._vision.provider_name,
                    error=str(exc),
                )
            except Exception:
                pass
            return SpecialistResult(
                specialist=self.name,
                status=AnalysisStatus.FAILED,
                answer="",
                error=f"Vision provider error: {exc}",
                raw_confidence=0.0,
                metadata={
                    "task": "grounding",
                    "provider": self._vision.provider_name,
                },
            )

        # ---- 4. Extract raw coordinates from provider output ---------------
        raw_box: Any = None
        box_format: str | None = result.get("coordinate_format")

        if "bbox" in result and result["bbox"] is not None:
            raw_box = result["bbox"]
        elif "box_2d" in result and result["box_2d"] is not None:
            raw_box = result["box_2d"]
            box_format = "box_2d"
        elif "box" in result and result["box"] is not None:
            raw_box = result["box"]
        elif "coordinates" in result and result["coordinates"] is not None:
            raw_box = result["coordinates"]

        # Check evidence list if top-level has no box
        if raw_box is None and "evidence" in result and isinstance(result["evidence"], list):
            for ev in result["evidence"]:
                if isinstance(ev, dict):
                    if "bbox" in ev and ev["bbox"] is not None:
                        raw_box = ev["bbox"]
                        break
                    elif "box_2d" in ev and ev["box_2d"] is not None:
                        raw_box = ev["box_2d"]
                        box_format = "box_2d"
                        break

        # Check answer text if structured fields are absent
        if raw_box is None and "answer" in result and isinstance(result["answer"], str):
            match = re.search(
                r"\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]",
                result["answer"],
            )
            if match:
                raw_box = [float(match.group(i)) for i in range(1, 5)]

        # Never fabricate: if missing, fail gracefully
        if raw_box is None:
            return SpecialistResult(
                specialist=self.name,
                status=AnalysisStatus.FAILED,
                answer="",
                error=f"No bounding box coordinates returned by vision provider for '{query}'.",
                raw_confidence=0.0,
                metadata={
                    "task": "grounding",
                    "provider": self._vision.provider_name,
                    "query": query,
                },
            )

        # ---- 5 & 6. Parse and validate coordinate representation -----------
        parsed_box, parse_error = parse_bounding_box(
            raw_box=raw_box,
            image_width=image_meta.width,
            image_height=image_meta.height,
            coordinate_format=box_format,
        )

        if parsed_box is None:
            return SpecialistResult(
                specialist=self.name,
                status=AnalysisStatus.FAILED,
                answer="",
                error=f"Malformed bounding box coordinates from provider: {parse_error}",
                raw_confidence=0.0,
                metadata={
                    "task": "grounding",
                    "provider": self._vision.provider_name,
                    "raw_box": str(raw_box),
                    "query": query,
                },
            )

        # ---- 7. Construct successful SpecialistResult with Evidence --------
        x1, y1, x2, y2 = parsed_box
        raw_confidence = float(result.get("confidence", 0.80))

        evidence = Evidence(
            evidence_id=uuid.uuid4().hex,
            specialist=self.name,
            source=self._vision.provider_name,
            claim=f"Localized '{query}' in image pixel space: [{x1}, {y1}, {x2}, {y2}]",
            evidence_type=EvidenceType.BBOX,
            bbox=[x1, y1, x2, y2],
            confidence=raw_confidence,
            metadata={
                "coordinate_space": "image_pixel_coordinates",
                "format": "[x1, y1, x2, y2]",
                "width_px": x2 - x1,
                "height_px": y2 - y1,
            },
        )

        answer = (
            f"The region corresponding to '{query}' has been localized at "
            f"[{x1}, {y1}, {x2}, {y2}] (x1, y1, x2, y2 in image pixel coordinates)."
        )

        return SpecialistResult(
            specialist=self.name,
            status=AnalysisStatus.SUCCESS,
            answer=answer,
            evidence=[evidence],
            raw_confidence=raw_confidence,
            metadata={
                "task": "grounding",
                "provider": self._vision.provider_name,
                "model": result.get("model", ""),
                "bbox": [x1, y1, x2, y2],
                "query": query,
                "coordinate_space": "image_pixel_coordinates",
                "image_filename": image_meta.filename,
            },
        )


# ---------------------------------------------------------------------------
# Backward-compatible Mock Specialist for Registry bootstrap
# ---------------------------------------------------------------------------

_GROUNDING_FIXTURES: dict[str, dict] = {
    "water": {"bbox": [380, 280, 1150, 880], "label": "Water body"},
    "lake": {"bbox": [380, 280, 1150, 880], "label": "Water body / Lake"},
    "river": {"bbox": [600, 400, 900, 1200], "label": "River channel"},
    "building": {"bbox": [0, 900, 600, 1440], "label": "Built-up / Buildings"},
    "vegetation": {"bbox": [900, 0, 1920, 600], "label": "Vegetated area"},
    "road": {"bbox": [200, 600, 800, 700], "label": "Road network"},
}

_DEFAULT_GROUND = {"bbox": [400, 400, 1200, 900], "label": "Region of interest"}


class MockGroundingSpecialist(Specialist):
    """Legacy mock specialist for backward compatibility with bootstrap()."""

    @property
    def name(self) -> str:
        return "mock_grounding"

    @property
    def capabilities(self) -> list[str]:
        return [Capability.GROUNDING]

    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        await asyncio.sleep(0.12)
        query_lower = request.query.lower()

        matched = None
        matched_key = None
        for keyword, fixture in _GROUNDING_FIXTURES.items():
            if keyword in query_lower:
                matched = fixture
                matched_key = keyword
                break

        if not matched:
            matched = _DEFAULT_GROUND
            matched_key = "region"

        answer = (
            f"The region corresponding to '{matched_key}' has been localized "
            f"in the image. The bounding box coordinates are "
            f"[{matched['bbox'][0]}, {matched['bbox'][1]}, "
            f"{matched['bbox'][2]}, {matched['bbox'][3]}] (x1, y1, x2, y2 in pixels). "
            f"Label: {matched['label']}."
        )

        evidence = Evidence(
            evidence_id=uuid.uuid4().hex,
            specialist=self.name,
            source="mock_grounding_model",
            claim=f"Grounded region: {matched['label']}",
            evidence_type=EvidenceType.BBOX,
            bbox=matched["bbox"],
            confidence=0.80,
        )

        return SpecialistResult(
            specialist=self.name,
            status=AnalysisStatus.SUCCESS,
            answer=answer,
            evidence=[evidence],
            raw_confidence=0.80,
            metadata={
                "grounded_label": matched["label"],
                "provider": "mock",
            },
        )
