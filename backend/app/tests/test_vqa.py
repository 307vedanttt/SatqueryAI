"""
SatQuery AI — Tests: VQA Specialist

Tests for the single-image VQA specialist:
  - Correct response structure on success
  - Rejection of invalid image counts (0, 2+)
  - Provider/model failure handling
  - Evidence extraction
  - Provider metadata preservation
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any
from unittest.mock import AsyncMock

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
from app.specialists.vqa import VQASpecialist


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(
    query: str = "What land cover types are visible?",
    n_images: int = 1,
) -> SpecialistRequest:
    """Build a SpecialistRequest with the given number of images."""
    metadata = [
        ImageMetadata(
            filename=f"image_{i}.tif",
            is_geotiff=True,
            crs="EPSG:4326",
            image_type="optical",
            sensor="Sentinel-2",
            acquisition_date="2024-06-15",
        )
        for i in range(n_images)
    ]
    return SpecialistRequest(
        request_id=uuid.uuid4().hex,
        specialist_name="vqa",
        input_configuration=InputConfiguration.SINGLE_OPTICAL,
        intent=QueryIntent.VQA,
        file_ids=[f"file_{i}" for i in range(n_images)],
        file_paths=[f"/data/uploads/image_{i}.tif" for i in range(n_images)],
        metadata=metadata,
        query=query,
    )


class _FailingVisionProvider(VisionProvider):
    """A vision provider that always raises an exception."""

    @property
    def provider_name(self) -> str:
        return "failing_test_provider"

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise RuntimeError("Simulated provider failure")

    async def health_check(self) -> bool:
        return False


class _EmptyAnswerProvider(VisionProvider):
    """A vision provider that returns an empty answer."""

    @property
    def provider_name(self) -> str:
        return "empty_answer_provider"

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {"answer": "", "confidence": 0.0, "evidence": []}

    async def health_check(self) -> bool:
        return True


class _RichEvidenceProvider(VisionProvider):
    """A provider that returns multiple evidence items with varied types."""

    @property
    def provider_name(self) -> str:
        return "rich_evidence_provider"

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "answer": "The image shows a water body and vegetation.",
            "confidence": 0.88,
            "evidence": [
                {
                    "claim": "Water body detected",
                    "bbox": [100, 200, 500, 600],
                    "confidence": 0.92,
                    "evidence_type": "bbox",
                },
                {
                    "claim": "Vegetation cover in northern region",
                    "confidence": 0.85,
                    "evidence_type": "region",
                },
                {
                    "claim": "Model-level prediction",
                    "confidence": 0.80,
                    # no evidence_type → should default to MODEL_PREDICTION
                },
            ],
            "provider": "rich_evidence_provider",
            "model": "test-vision-v2",
        }

    async def health_check(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestVQASpecialist:
    """Tests for VQASpecialist."""

    # -- Success cases -------------------------------------------------------

    @pytest.mark.asyncio
    async def test_successful_vqa_with_mock_provider(self):
        """VQA with the project's MockVisionProvider produces a valid result."""
        provider = MockVisionProvider()
        specialist = VQASpecialist(vision_provider=provider)
        request = _make_request(query="Describe the land cover visible.")

        result = await specialist.execute(request)

        assert isinstance(result, SpecialistResult)
        assert result.status == AnalysisStatus.SUCCESS
        assert result.specialist == "vqa"
        assert len(result.answer) > 0
        assert result.raw_confidence > 0.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_response_contains_provider_metadata(self):
        """The result metadata preserves provider and model information."""
        provider = MockVisionProvider()
        specialist = VQASpecialist(vision_provider=provider)
        request = _make_request()

        result = await specialist.execute(request)

        assert result.metadata["provider"] == "mock"
        assert "model" in result.metadata
        assert result.metadata["input_configuration"] == "SINGLE_OPTICAL"
        assert result.metadata["intent"] == "VQA"
        assert result.metadata["image_filename"] == "image_0.tif"

    @pytest.mark.asyncio
    async def test_evidence_extracted_from_provider_output(self):
        """Evidence items from the provider are mapped to typed Evidence."""
        provider = MockVisionProvider()
        specialist = VQASpecialist(vision_provider=provider)
        request = _make_request()

        result = await specialist.execute(request)

        assert len(result.evidence) >= 1
        ev = result.evidence[0]
        assert ev.specialist == "vqa"
        assert ev.source == "mock"
        assert len(ev.claim) > 0
        assert 0.0 <= ev.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_rich_evidence_types(self):
        """Multiple evidence items with different types are handled correctly."""
        provider = _RichEvidenceProvider()
        specialist = VQASpecialist(vision_provider=provider)
        request = _make_request()

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.SUCCESS
        assert len(result.evidence) == 3

        # First: has bbox → should be BBOX type
        assert result.evidence[0].evidence_type == EvidenceType.BBOX
        assert result.evidence[0].bbox == [100, 200, 500, 600]

        # Second: explicit "region" type
        assert result.evidence[1].evidence_type == EvidenceType.REGION

        # Third: no type → should default to MODEL_PREDICTION
        assert result.evidence[2].evidence_type == EvidenceType.MODEL_PREDICTION

    @pytest.mark.asyncio
    async def test_model_field_in_metadata(self):
        """When provider returns a 'model' field, it's preserved."""
        provider = _RichEvidenceProvider()
        specialist = VQASpecialist(vision_provider=provider)
        request = _make_request()

        result = await specialist.execute(request)

        assert result.metadata["model"] == "test-vision-v2"

    # -- Invalid image count -------------------------------------------------

    @pytest.mark.asyncio
    async def test_zero_images_returns_error(self):
        """Requesting VQA with zero images returns FAILED status."""
        provider = MockVisionProvider()
        specialist = VQASpecialist(vision_provider=provider)
        request = _make_request(n_images=0)

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert result.error is not None
        assert "0" in result.error
        assert result.raw_confidence == 0.0

    @pytest.mark.asyncio
    async def test_two_images_returns_error(self):
        """Requesting VQA with two images returns FAILED status."""
        provider = MockVisionProvider()
        specialist = VQASpecialist(vision_provider=provider)
        request = _make_request(n_images=2)

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert result.error is not None
        assert "2" in result.error
        assert result.raw_confidence == 0.0

    @pytest.mark.asyncio
    async def test_three_images_returns_error(self):
        """Requesting VQA with three images returns FAILED status."""
        provider = MockVisionProvider()
        specialist = VQASpecialist(vision_provider=provider)
        request = _make_request(n_images=3)

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert "3" in result.error

    # -- Provider / model failure --------------------------------------------

    @pytest.mark.asyncio
    async def test_provider_exception_returns_error_not_crash(self):
        """When the provider raises, VQA returns FAILED without crashing."""
        provider = _FailingVisionProvider()
        specialist = VQASpecialist(vision_provider=provider)
        request = _make_request()

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert result.error is not None
        assert "provider" in result.error.lower() or "Simulated" in result.error
        assert result.raw_confidence == 0.0
        assert result.metadata["provider"] == "failing_test_provider"

    @pytest.mark.asyncio
    async def test_empty_answer_returns_error(self):
        """When the provider returns an empty answer string, status is FAILED."""
        provider = _EmptyAnswerProvider()
        specialist = VQASpecialist(vision_provider=provider)
        request = _make_request()

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert result.error is not None
        assert "empty" in result.error.lower()

    # -- Specialist interface ------------------------------------------------

    def test_specialist_name(self):
        """The specialist name is 'vqa'."""
        specialist = VQASpecialist(vision_provider=MockVisionProvider())
        assert specialist.name == "vqa"

    def test_specialist_capabilities(self):
        """VQA specialist declares the expected capabilities."""
        specialist = VQASpecialist(vision_provider=MockVisionProvider())
        caps = specialist.capabilities
        assert "vqa" in caps
        assert "scene_description" in caps

    def test_specialist_repr(self):
        """repr includes the specialist name."""
        specialist = VQASpecialist(vision_provider=MockVisionProvider())
        assert "vqa" in repr(specialist)

    # -- Query passthrough ---------------------------------------------------

    @pytest.mark.asyncio
    async def test_user_query_is_passed_to_provider(self):
        """The user's question is forwarded to the provider, not replaced."""
        captured_prompt = {}

        class _CapturingProvider(VisionProvider):
            @property
            def provider_name(self) -> str:
                return "capturing"

            async def analyze_image(self, image_path, prompt, metadata=None):
                captured_prompt["prompt"] = prompt
                return {
                    "answer": "Response to the specific question.",
                    "confidence": 0.75,
                    "evidence": [],
                }

            async def health_check(self):
                return True

        specialist = VQASpecialist(vision_provider=_CapturingProvider())
        query = "How many buildings are visible in the northeastern quadrant?"
        request = _make_request(query=query)

        await specialist.execute(request)

        assert captured_prompt["prompt"] == query
