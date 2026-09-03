"""
SatQuery AI — Tests: Single-Image Grounding Specialist

Comprehensive pytest suite testing:
  - Valid bounding box parsing and evidence generation (pixel, Gemini 1000, dict, normalized)
  - Rejection of malformed coordinates (inverted bounds, negative, wrong count, non-numeric, out-of-bounds)
  - Graceful handling of missing coordinates without fabrication
  - Invalid image count rejection (0, 2, 3 images)
  - Provider and model failure handling
  - Empty query validation
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from app.models.schemas import (
    AnalysisStatus,
    EvidenceType,
    ImageMetadata,
    InputConfiguration,
    QueryIntent,
    SpecialistRequest,
    SpecialistResult,
)
from app.providers.base import VisionProvider
from app.providers.mock_provider import MockVisionProvider
from app.specialists.grounding import (
    GroundingSpecialist,
    parse_bounding_box,
)


# ---------------------------------------------------------------------------
# Test Helpers & Stubs
# ---------------------------------------------------------------------------

def _make_grounding_request(
    query: str = "Locate the primary reservoir",
    n_images: int = 1,
    width: int = 1920,
    height: int = 1080,
) -> SpecialistRequest:
    """Construct a typed SpecialistRequest for grounding."""
    metadata = [
        ImageMetadata(
            filename=f"satellite_tile_{i}.tif",
            width=width,
            height=height,
            is_geotiff=True,
            crs="EPSG:32643",
            image_type="optical",
            sensor="Sentinel-2",
        )
        for i in range(n_images)
    ]
    return SpecialistRequest(
        request_id=uuid.uuid4().hex,
        specialist_name="grounding",
        input_configuration=InputConfiguration.SINGLE_OPTICAL,
        intent=QueryIntent.GROUNDING,
        file_ids=[f"file_{i}" for i in range(n_images)],
        file_paths=[f"/data/uploads/satellite_tile_{i}.tif" for i in range(n_images)],
        metadata=metadata,
        query=query,
    )


class _CustomBoxProvider(VisionProvider):
    """Vision provider returning a controlled bounding box structure."""

    def __init__(self, box_payload: dict[str, Any]) -> None:
        self.payload = box_payload

    @property
    def provider_name(self) -> str:
        return "custom_box_provider"

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        base = {
            "answer": "Target localized.",
            "confidence": 0.89,
            "provider": self.provider_name,
            "model": "grounding-vision-v1",
        }
        base.update(self.payload)
        return base

    async def health_check(self) -> bool:
        return True


class _FailingGroundingProvider(VisionProvider):
    @property
    def provider_name(self) -> str:
        return "failing_provider"

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise ConnectionResetError("Remote vision model connection failed.")

    async def health_check(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# Unit Tests for Coordinate Parser
# ---------------------------------------------------------------------------

class TestParseBoundingBox:
    """Direct tests for coordinate format parsing and validation."""

    def test_valid_pixel_box(self):
        box, err = parse_bounding_box([100, 150, 400, 600], image_width=1920, image_height=1080)
        assert err is None
        assert box == [100, 150, 400, 600]

    def test_valid_gemini_1000_box(self):
        # [ymin, xmin, ymax, xmax] in 0..1000 scale
        # on 1000x1000: ymin=100, xmin=200, ymax=500, xmax=800 -> [200, 100, 800, 500]
        box, err = parse_bounding_box(
            [100, 200, 500, 800],
            image_width=1000,
            image_height=1000,
            coordinate_format="box_2d",
        )
        assert err is None
        assert box == [200, 100, 800, 500]

    def test_valid_dict_box(self):
        box, err = parse_bounding_box({"x1": 50, "y1": 60, "x2": 300, "y2": 400})
        assert err is None
        assert box == [50, 60, 300, 400]

    def test_valid_string_box(self):
        box, err = parse_bounding_box("[120, 240, 600, 800]")
        assert err is None
        assert box == [120, 240, 600, 800]

    def test_malformed_inverted_x(self):
        # x1 >= x2
        box, err = parse_bounding_box([500, 100, 200, 300])
        assert box is None
        assert "width" in err.lower() or "x1" in err

    def test_malformed_inverted_y(self):
        # y1 >= y2
        box, err = parse_bounding_box([100, 500, 200, 300])
        assert box is None
        assert "height" in err.lower() or "y1" in err

    def test_malformed_negative_coordinates(self):
        box, err = parse_bounding_box([-10, 100, 200, 300])
        assert box is None
        assert "negative" in err.lower()

    def test_malformed_wrong_count(self):
        box, err = parse_bounding_box([100, 200, 300])
        assert box is None
        assert "4 coordinates" in err

    def test_malformed_non_numeric(self):
        box, err = parse_bounding_box([100, "invalid", 300, 400])
        assert box is None
        assert "numeric" in err.lower()

    def test_malformed_outside_image(self):
        # origin outside 500x500
        box, err = parse_bounding_box([600, 700, 800, 900], image_width=500, image_height=500)
        assert box is None
        assert "outside image" in err.lower()


# ---------------------------------------------------------------------------
# Integration Tests for GroundingSpecialist
# ---------------------------------------------------------------------------

class TestGroundingSpecialist:
    """Full execution tests for GroundingSpecialist."""

    # -- 1. Valid Bounding Box -----------------------------------------------

    @pytest.mark.asyncio
    async def test_successful_grounding_with_mock_provider(self):
        """Standard grounding query produces valid image-space Evidence."""
        provider = MockVisionProvider()
        specialist = GroundingSpecialist(vision_provider=provider)
        request = _make_grounding_request(query="water body")

        result = await specialist.execute(request)

        assert isinstance(result, SpecialistResult)
        assert result.status == AnalysisStatus.SUCCESS
        assert result.specialist == "grounding"
        assert len(result.evidence) == 1

        ev = result.evidence[0]
        assert ev.evidence_type == EvidenceType.BBOX
        assert ev.bbox is not None
        assert len(ev.bbox) == 4
        # Verify valid non-empty box
        x1, y1, x2, y2 = ev.bbox
        assert x1 < x2 and y1 < y2
        assert x1 >= 0 and y1 >= 0
        assert ev.metadata["coordinate_space"] == "image_pixel_coordinates"
        assert result.metadata["coordinate_space"] == "image_pixel_coordinates"

    @pytest.mark.asyncio
    async def test_valid_bounding_box_from_custom_provider(self):
        """Custom valid bbox [250, 180, 850, 700] is faithfully mapped."""
        provider = _CustomBoxProvider({"bbox": [250, 180, 850, 700]})
        specialist = GroundingSpecialist(vision_provider=provider)
        request = _make_grounding_request(query="aircraft hangar")

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.SUCCESS
        assert result.evidence[0].bbox == [250, 180, 850, 700]
        assert result.metadata["bbox"] == [250, 180, 850, 700]
        assert "hangar" in result.answer

    @pytest.mark.asyncio
    async def test_valid_gemini_box_2d_conversion(self):
        """Gemini-style box_2d [ymin, xmin, ymax, xmax] in 0..1000 scales correctly."""
        # 1920x1080: ymin=100 (108px), xmin=200 (384px), ymax=600 (648px), xmax=500 (960px)
        provider = _CustomBoxProvider({
            "box_2d": [100, 200, 600, 500],
            "coordinate_format": "box_2d",
        })
        specialist = GroundingSpecialist(vision_provider=provider)
        request = _make_grounding_request(width=1920, height=1080)

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.SUCCESS
        bbox = result.evidence[0].bbox
        assert bbox == [384, 108, 960, 648]

    # -- 2. Malformed Coordinates --------------------------------------------

    @pytest.mark.asyncio
    async def test_malformed_inverted_coordinates_rejected(self):
        """Inverted bounds (x1 >= x2) produce FAILED status without fabrication."""
        provider = _CustomBoxProvider({"bbox": [800, 200, 300, 500]})
        specialist = GroundingSpecialist(vision_provider=provider)
        request = _make_grounding_request()

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert result.answer == ""
        assert len(result.evidence) == 0
        assert "Malformed" in result.error

    @pytest.mark.asyncio
    async def test_malformed_non_numeric_coordinates_rejected(self):
        """Non-numeric coordinates produce FAILED status."""
        provider = _CustomBoxProvider({"bbox": [100, "bad_coord", 300, 400]})
        specialist = GroundingSpecialist(vision_provider=provider)
        request = _make_grounding_request()

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert result.answer == ""
        assert "Malformed" in result.error

    @pytest.mark.asyncio
    async def test_malformed_three_coordinates_rejected(self):
        """Incomplete 3-coordinate box produces FAILED status."""
        provider = _CustomBoxProvider({"bbox": [100, 200, 300]})
        specialist = GroundingSpecialist(vision_provider=provider)
        request = _make_grounding_request()

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert "Malformed" in result.error

    # -- 3. Missing Coordinates ----------------------------------------------

    @pytest.mark.asyncio
    async def test_missing_coordinates_never_fabricated(self):
        """When provider returns answer without coordinates, fail gracefully."""
        provider = _CustomBoxProvider({"answer": "I see a building in the image.", "bbox": None, "evidence": []})
        specialist = GroundingSpecialist(vision_provider=provider)
        request = _make_grounding_request()

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert result.answer == ""
        assert len(result.evidence) == 0
        assert "No bounding box" in result.error
        assert result.raw_confidence == 0.0

    # -- 4. Invalid Image Count ----------------------------------------------

    @pytest.mark.asyncio
    async def test_zero_images_rejected(self):
        """Zero images returns FAILED status."""
        specialist = GroundingSpecialist(vision_provider=MockVisionProvider())
        request = _make_grounding_request(n_images=0)

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert "0" in result.error

    @pytest.mark.asyncio
    async def test_two_images_rejected(self):
        """Two images returns FAILED status."""
        specialist = GroundingSpecialist(vision_provider=MockVisionProvider())
        request = _make_grounding_request(n_images=2)

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert "2" in result.error

    @pytest.mark.asyncio
    async def test_three_images_rejected(self):
        """Three images returns FAILED status."""
        specialist = GroundingSpecialist(vision_provider=MockVisionProvider())
        request = _make_grounding_request(n_images=3)

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert "3" in result.error

    # -- 5. Provider / Model Failure -----------------------------------------

    @pytest.mark.asyncio
    async def test_provider_exception_returns_failure_not_crash(self):
        """When provider raises, FAILED status is returned without fabrication."""
        specialist = GroundingSpecialist(vision_provider=_FailingGroundingProvider())
        request = _make_grounding_request()

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert result.answer == ""
        assert len(result.evidence) == 0
        assert "Vision provider error" in result.error

    # -- 6. Empty Query Handling ---------------------------------------------

    @pytest.mark.asyncio
    async def test_empty_query_rejected(self):
        """Empty query produces FAILED status."""
        specialist = GroundingSpecialist(vision_provider=MockVisionProvider())
        request = _make_grounding_request(query="")

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert "query" in result.error.lower()

    # -- 7. Specialist Properties --------------------------------------------

    def test_specialist_properties(self):
        specialist = GroundingSpecialist(vision_provider=MockVisionProvider())
        assert specialist.name == "grounding"
        assert "grounding" in specialist.capabilities
