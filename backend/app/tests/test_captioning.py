"""
SatQuery AI — Tests: Captioning / Scene Description Specialist

Tests for the single-image captioning specialist:
  - Correct response structure and task identification
  - Use of standard remote-sensing instruction
  - Rejection of invalid image counts (0, 2+)
  - Handling of provider/model failure without fabricating captions
  - Evidence and confidence mapping
  - Faithful reporting of remote_sensing_adapted flag
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
from app.specialists.captioning import (
    DEFAULT_CAPTION_INSTRUCTION,
    CaptioningSpecialist,
)


# ---------------------------------------------------------------------------
# Helpers & Test Providers
# ---------------------------------------------------------------------------

def _make_request(
    query: str = "",
    n_images: int = 1,
) -> SpecialistRequest:
    """Build a SpecialistRequest for captioning."""
    metadata = [
        ImageMetadata(
            filename=f"satellite_tile_{i}.tif",
            is_geotiff=True,
            crs="EPSG:32643",
            image_type="optical",
            sensor="Sentinel-2",
            acquisition_date="2024-05-10",
        )
        for i in range(n_images)
    ]
    return SpecialistRequest(
        request_id=uuid.uuid4().hex,
        specialist_name="captioning",
        input_configuration=InputConfiguration.SINGLE_OPTICAL,
        intent=QueryIntent.SCENE_DESCRIPTION,
        file_ids=[f"file_{i}" for i in range(n_images)],
        file_paths=[f"/data/uploads/satellite_tile_{i}.tif" for i in range(n_images)],
        metadata=metadata,
        query=query,
    )


class _FailingVisionProvider(VisionProvider):
    @property
    def provider_name(self) -> str:
        return "failing_provider"

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise ConnectionError("Vision model inference timeout / failure")

    async def health_check(self) -> bool:
        return False


class _EmptyAnswerProvider(VisionProvider):
    @property
    def provider_name(self) -> str:
        return "empty_provider"

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {"answer": "", "confidence": 0.0, "evidence": []}

    async def health_check(self) -> bool:
        return True


class _PromptCapturingProvider(VisionProvider):
    def __init__(self, is_rs_adapted: bool = False) -> None:
        self.captured_prompt: str | None = None
        self.is_rs_adapted = is_rs_adapted

    @property
    def provider_name(self) -> str:
        return "prompt_capturing_provider"

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.captured_prompt = prompt
        return {
            "answer": "Dense vegetation occupies the northern region with agricultural parcels to the south.",
            "confidence": 0.86,
            "evidence": [
                {
                    "claim": "Dense vegetation zone",
                    "bbox": [0, 0, 1000, 500],
                    "confidence": 0.88,
                    "evidence_type": "bbox",
                }
            ],
            "model": "rs-adapted-vit-b",
            "is_rs_adapted": self.is_rs_adapted,
        }

    async def health_check(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCaptioningSpecialist:
    """Test suite for single-image captioning specialist."""

    @pytest.mark.asyncio
    async def test_successful_captioning_with_mock_provider(self):
        """Standard captioning produces a valid SpecialistResult."""
        provider = MockVisionProvider()
        specialist = CaptioningSpecialist(vision_provider=provider)
        request = _make_request(query="")

        result = await specialist.execute(request)

        assert isinstance(result, SpecialistResult)
        assert result.status == AnalysisStatus.SUCCESS
        assert result.specialist == "captioning"
        assert len(result.answer) > 0
        assert result.raw_confidence > 0.0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_task_identification_and_metadata(self):
        """Response clearly identifies task='captioning/scene description' and provider."""
        provider = MockVisionProvider()
        specialist = CaptioningSpecialist(vision_provider=provider)
        request = _make_request(query="")

        result = await specialist.execute(request)

        assert result.metadata["task"] == "captioning/scene description"
        assert result.metadata["provider"] == "mock"
        assert "model" in result.metadata
        assert result.metadata["remote_sensing_adapted"] is False
        assert result.metadata["instruction"] == DEFAULT_CAPTION_INSTRUCTION

    @pytest.mark.asyncio
    async def test_default_remote_sensing_instruction_used_when_empty(self):
        """When query is empty, default RS instruction is used."""
        provider = _PromptCapturingProvider()
        specialist = CaptioningSpecialist(vision_provider=provider)
        request = _make_request(query="")

        await specialist.execute(request)

        assert provider.captured_prompt == DEFAULT_CAPTION_INSTRUCTION
        assert "Describe the land cover and major objects" in provider.captured_prompt

    @pytest.mark.asyncio
    async def test_generic_query_replaced_by_rs_instruction(self):
        """Generic keywords like 'describe this image' trigger the RS instruction."""
        provider = _PromptCapturingProvider()
        specialist = CaptioningSpecialist(vision_provider=provider)
        request = _make_request(query="describe this image")

        await specialist.execute(request)

        assert provider.captured_prompt == DEFAULT_CAPTION_INSTRUCTION

    @pytest.mark.asyncio
    async def test_custom_scene_description_query_respected(self):
        """Specific user scene description queries are passed to the provider."""
        provider = _PromptCapturingProvider()
        specialist = CaptioningSpecialist(vision_provider=provider)
        custom_query = "Provide a detailed overview of urban density and road networks."
        request = _make_request(query=custom_query)

        await specialist.execute(request)

        assert provider.captured_prompt == custom_query

    @pytest.mark.asyncio
    async def test_evidence_structure_preserved(self):
        """Evidence returned by provider is mapped to Evidence objects."""
        provider = _PromptCapturingProvider()
        specialist = CaptioningSpecialist(vision_provider=provider)
        request = _make_request()

        result = await specialist.execute(request)

        assert len(result.evidence) == 1
        ev = result.evidence[0]
        assert ev.specialist == "captioning"
        assert ev.source == "prompt_capturing_provider"
        assert ev.evidence_type == EvidenceType.BBOX
        assert ev.bbox == [0, 0, 1000, 500]
        assert ev.confidence == 0.88

    @pytest.mark.asyncio
    async def test_rs_adapted_flag_reported_accurately(self):
        """Does not claim RS specialization unless provider actually has it."""
        # Generic provider
        p_generic = _PromptCapturingProvider(is_rs_adapted=False)
        res_generic = await CaptioningSpecialist(p_generic).execute(_make_request())
        assert res_generic.metadata["remote_sensing_adapted"] is False

        # Adapted provider
        p_adapted = _PromptCapturingProvider(is_rs_adapted=True)
        res_adapted = await CaptioningSpecialist(p_adapted).execute(_make_request())
        assert res_adapted.metadata["remote_sensing_adapted"] is True

    # -- Invalid image count rejection ---------------------------------------

    @pytest.mark.asyncio
    async def test_zero_images_rejected(self):
        """Zero images returns FAILED status."""
        specialist = CaptioningSpecialist(vision_provider=MockVisionProvider())
        request = _make_request(n_images=0)

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert "0" in result.error
        assert result.answer == ""
        assert result.raw_confidence == 0.0
        assert result.metadata["task"] == "captioning/scene description"

    @pytest.mark.asyncio
    async def test_two_images_rejected(self):
        """Two images returns FAILED status."""
        specialist = CaptioningSpecialist(vision_provider=MockVisionProvider())
        request = _make_request(n_images=2)

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert "2" in result.error
        assert result.answer == ""

    # -- Failure handling without fabricating --------------------------------

    @pytest.mark.asyncio
    async def test_provider_error_does_not_fabricate_caption(self):
        """When provider fails, caption is NOT fabricated; error status returned."""
        specialist = CaptioningSpecialist(vision_provider=_FailingVisionProvider())
        request = _make_request()

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert result.answer == ""  # Never fabricated
        assert result.error is not None
        assert "Vision provider error" in result.error
        assert result.raw_confidence == 0.0

    @pytest.mark.asyncio
    async def test_empty_answer_does_not_fabricate_caption(self):
        """When provider returns empty string, error status returned."""
        specialist = CaptioningSpecialist(vision_provider=_EmptyAnswerProvider())
        request = _make_request()

        result = await specialist.execute(request)

        assert result.status == AnalysisStatus.FAILED
        assert result.answer == ""
        assert "empty" in result.error.lower()

    # -- Specialist metadata -------------------------------------------------

    def test_specialist_properties(self):
        specialist = CaptioningSpecialist(vision_provider=MockVisionProvider())
        assert specialist.name == "captioning"
        assert "scene_description" in specialist.capabilities
        assert "CaptioningSpecialist" in repr(specialist)
