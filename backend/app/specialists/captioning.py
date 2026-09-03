"""
SatQuery AI — Single-Image Captioning / Scene Description Specialist

Generates natural language scene descriptions and land-cover captions
for exactly ONE remote-sensing image using the project's VisionProvider
abstraction.

In DEMO_MODE, the mock vision provider is used; with an external provider
configured, the same interface delegates to real vision APIs.

Key properties:
  - Accepts exactly one image (rejects 0 or 2+)
  - Uses the canonical remote-sensing instruction:
    "Describe the land cover and major objects visible in this image."
    (or user-specified query if provided)
  - Returns the project's SpecialistResult contract
  - Explicitly flags task as "captioning/scene description"
  - Does NOT claim remote-sensing specialization unless provider is explicitly adapted
  - Does NOT fabricate a caption on failure (returns status=FAILED)
  - Maps provider evidence and confidence faithfully
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.models.schemas import (
    AnalysisStatus,
    SpecialistRequest,
    SpecialistResult,
)
from app.providers.base import VisionProvider
from app.registry.capabilities import Capability
from app.specialists.base import Specialist
from app.specialists.vqa import _extract_evidence

logger = get_logger(__name__)

DEFAULT_CAPTION_INSTRUCTION = (
    "Describe the land cover and major objects visible in this image."
)


class CaptioningSpecialist(Specialist):
    """
    Single-image scene description and captioning specialist.

    Delegates inference to a VisionProvider instance.

    Parameters
    ----------
    vision_provider : VisionProvider
        The provider instance to use for image analysis.
    name : str, default "captioning"
        Identifier for this specialist.
    """

    def __init__(
        self,
        vision_provider: VisionProvider,
        name: str = "captioning",
    ) -> None:
        self._vision = vision_provider
        self._name = name

    # -- Specialist interface ------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> list[str]:
        return [Capability.SCENE_DESCRIPTION]

    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        """
        Run single-image captioning/scene description.

        Precondition: exactly one image in the request.
        """
        # ---- Validate: exactly one image -----------------------------------
        n_images = len(request.metadata)
        if n_images != 1:
            return SpecialistResult(
                specialist=self.name,
                status=AnalysisStatus.FAILED,
                answer="",
                error=(
                    f"Captioning requires exactly 1 image, but {n_images} "
                    f"{'were' if n_images != 1 else 'was'} provided."
                ),
                raw_confidence=0.0,
                metadata={
                    "task": "captioning/scene description",
                    "provider": self._vision.provider_name,
                },
            )

        image_path = request.file_paths[0]
        image_meta = request.metadata[0]

        # Determine prompt: use remote-sensing standard instruction if query is
        # empty or generic
        query = request.query.strip() if request.query else ""
        if not query or query.lower() in {
            "caption",
            "describe",
            "describe image",
            "describe this image",
            "scene description",
            "caption this image",
        }:
            prompt = DEFAULT_CAPTION_INSTRUCTION
        else:
            prompt = query

        # Build metadata hints for the vision provider
        meta_hints: dict[str, Any] = {
            "filename": image_meta.filename,
            "image_type": image_meta.image_type,
            "crs": image_meta.crs,
            "sensor": image_meta.sensor,
            "acquisition_date": image_meta.acquisition_date,
            "task": "captioning/scene description",
        }

        # ---- Call the vision provider --------------------------------------
        try:
            result = await self._vision.analyze_image(
                image_path=image_path,
                prompt=prompt,
                metadata=meta_hints,
            )
        except Exception as exc:
            try:
                logger.error(
                    "captioning_provider_error",
                    provider=self._vision.provider_name,
                    error=str(exc),
                )
            except Exception:
                pass  # Do not let logging failure suppress error result
            return SpecialistResult(
                specialist=self.name,
                status=AnalysisStatus.FAILED,
                answer="",
                error=f"Vision provider error: {exc}",
                raw_confidence=0.0,
                metadata={
                    "task": "captioning/scene description",
                    "provider": self._vision.provider_name,
                },
            )

        # ---- Check answer from provider (never fabricate) ------------------
        answer = result.get("answer", "")
        if not answer:
            return SpecialistResult(
                specialist=self.name,
                status=AnalysisStatus.FAILED,
                answer="",
                error="Vision provider returned an empty caption.",
                raw_confidence=0.0,
                metadata={
                    "task": "captioning/scene description",
                    "provider": self._vision.provider_name,
                },
            )

        raw_confidence: float = float(result.get("confidence", 0.0))

        # Check if model is actually remote-sensing specialized
        # Only claim RS specialization if explicitly marked on the provider or model result
        is_rs_adapted = bool(
            result.get("is_rs_adapted", False)
            or getattr(self._vision, "is_rs_adapted", False)
        )

        # Build typed Evidence list
        evidence_items = _extract_evidence(
            raw_evidence=result.get("evidence", []),
            specialist_name=self.name,
            provider_name=self._vision.provider_name,
        )

        return SpecialistResult(
            specialist=self.name,
            status=AnalysisStatus.SUCCESS,
            answer=answer,
            evidence=evidence_items,
            raw_confidence=raw_confidence,
            metadata={
                "task": "captioning/scene description",
                "provider": self._vision.provider_name,
                "model": result.get("model", ""),
                "remote_sensing_adapted": is_rs_adapted,
                "instruction": prompt,
                "input_configuration": (
                    request.input_configuration.value
                    if hasattr(request.input_configuration, "value")
                    else str(request.input_configuration)
                ),
                "intent": (
                    request.intent.value
                    if hasattr(request.intent, "value")
                    else str(request.intent)
                ),
                "image_filename": image_meta.filename,
            },
        )
