"""
SatQuery AI — Single-Image VQA Specialist

Performs visual question answering on exactly ONE image using the
project's VisionProvider abstraction.  In DEMO_MODE the mock provider
is used; with a real provider configured the same interface calls out
to the external API.

This specialist:
  - Accepts exactly one image (rejects 0 or 2+)
  - Delegates inference to VisionProvider.analyze_image()
  - Never fabricates or hardcodes satellite-image answers
  - Maps provider output to the project's SpecialistResult contract
  - Exposes evidence returned by the provider
  - Preserves provider/model metadata for auditability
  - Returns SpecialistResult(status=FAILED) on provider errors
"""

from __future__ import annotations

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

# Maximum number of evidence items to extract from the provider response
_MAX_EVIDENCE_ITEMS = 20


class VQASpecialist(Specialist):
    """
    Single-image visual question answering specialist.

    Delegates image+question inference to a VisionProvider instance,
    so the same specialist works with mock, OpenAI, Gemini, etc.

    Parameters
    ----------
    vision_provider : VisionProvider
        The provider instance to use for image analysis.
    """

    def __init__(self, vision_provider: VisionProvider) -> None:
        self._vision = vision_provider

    # -- Specialist interface ------------------------------------------------

    @property
    def name(self) -> str:
        return "vqa"

    @property
    def capabilities(self) -> list[str]:
        return [
            Capability.VQA,
            Capability.SCENE_DESCRIPTION,
            Capability.OBJECT_IDENTIFICATION,
            Capability.BUILT_UP_ANALYSIS,
            Capability.WATER_ANALYSIS,
        ]

    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        """
        Run single-image VQA.

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
                    f"VQA requires exactly 1 image, but {n_images} "
                    f"{'were' if n_images != 1 else 'was'} provided."
                ),
                raw_confidence=0.0,
                metadata={"provider": self._vision.provider_name},
            )

        image_path = request.file_paths[0]
        image_meta = request.metadata[0]

        # Build metadata hints for the provider
        meta_hints: dict[str, Any] = {
            "filename": image_meta.filename,
            "image_type": image_meta.image_type,
            "crs": image_meta.crs,
            "sensor": image_meta.sensor,
            "acquisition_date": image_meta.acquisition_date,
        }

        # ---- Call the vision provider --------------------------------------
        try:
            result = await self._vision.analyze_image(
                image_path=image_path,
                prompt=request.query,
                metadata=meta_hints,
            )
        except Exception as exc:
            try:
                logger.error(
                    "vqa_provider_error",
                    provider=self._vision.provider_name,
                    error=str(exc),
                )
            except Exception:
                pass  # Never let logging prevent error result from returning
            return SpecialistResult(
                specialist=self.name,
                status=AnalysisStatus.FAILED,
                answer="",
                error=f"Vision provider error: {exc}",
                raw_confidence=0.0,
                metadata={"provider": self._vision.provider_name},
            )

        # ---- Map provider response to SpecialistResult ---------------------
        answer = result.get("answer", "")
        if not answer:
            return SpecialistResult(
                specialist=self.name,
                status=AnalysisStatus.FAILED,
                answer="",
                error="Vision provider returned an empty answer.",
                raw_confidence=0.0,
                metadata={"provider": self._vision.provider_name},
            )

        raw_confidence: float = float(result.get("confidence", 0.0))

        # Build typed Evidence list from provider output
        evidence_items: list[Evidence] = _extract_evidence(
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
                "provider": self._vision.provider_name,
                "model": result.get("model", ""),
                "input_configuration": request.input_configuration.value,
                "intent": request.intent.value,
                "image_filename": image_meta.filename,
            },
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_evidence(
    raw_evidence: list[dict[str, Any]],
    specialist_name: str,
    provider_name: str,
) -> list[Evidence]:
    """
    Convert the list-of-dicts evidence from the provider response into
    typed Evidence model instances.  Tolerant of missing/extra fields.
    """
    items: list[Evidence] = []
    for entry in raw_evidence[:_MAX_EVIDENCE_ITEMS]:
        try:
            # Determine evidence type
            raw_type = entry.get("evidence_type")
            if isinstance(raw_type, EvidenceType):
                ev_type = raw_type
            elif isinstance(raw_type, str):
                try:
                    ev_type = EvidenceType(raw_type)
                except ValueError:
                    ev_type = EvidenceType.MODEL_PREDICTION
            else:
                # Infer from presence of bbox
                ev_type = EvidenceType.BBOX if entry.get("bbox") else EvidenceType.MODEL_PREDICTION

            items.append(
                Evidence(
                    evidence_id=uuid.uuid4().hex,
                    specialist=specialist_name,
                    source=provider_name,
                    claim=str(entry.get("claim", "Feature identified")),
                    evidence_type=ev_type,
                    bbox=entry.get("bbox"),
                    confidence=float(entry.get("confidence", 0.0)),
                    metadata=entry.get("metadata", {}),
                )
            )
        except Exception:
            continue

    return items
