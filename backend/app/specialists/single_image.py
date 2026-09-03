"""
SatQuery AI — Mock Single Image Specialist

Returns realistic, structured mock responses for single-image analysis.
Mock responses correspond to predictable demo fixtures, not random data.

This specialist is a PLACEHOLDER for:
  - API-based vision specialist (Phase 8)
  - RS-adapted fine-tuned specialist (Phase 9)

No real AI inference occurs here.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from app.models.schemas import (
    AnalysisStatus,
    Evidence,
    EvidenceType,
    QueryIntent,
    SpecialistRequest,
    SpecialistResult,
)
from app.registry.capabilities import Capability
from app.specialists.base import Specialist

# --- Demo fixture responses keyed by intent ---
_FIXTURES: dict[str, dict] = {
    QueryIntent.SCENE_DESCRIPTION.value: {
        "answer": (
            "The image shows a complex landscape featuring a prominent water body "
            "occupying the central portion, surrounded by dense vegetated areas to "
            "the north and east. Built-up regions with rectangular structures are "
            "visible in the southwestern quadrant. Road networks connect the "
            "settlement areas. The terrain appears relatively flat with some "
            "elevation variation in the northern sector."
        ),
        "evidence": [
            {
                "claim": "Large central water body",
                "bbox": [380, 280, 1150, 880],
                "evidence_type": EvidenceType.BBOX,
                "confidence": 0.88,
            },
            {
                "claim": "Dense vegetation in northern and eastern regions",
                "bbox": [0, 0, 1920, 400],
                "evidence_type": EvidenceType.REGION,
                "confidence": 0.82,
            },
            {
                "claim": "Built-up settlement in southwestern quadrant",
                "bbox": [0, 900, 600, 1440],
                "evidence_type": EvidenceType.REGION,
                "confidence": 0.79,
            },
        ],
        "confidence": 0.84,
    },
    QueryIntent.VQA.value: {
        "answer": (
            "Based on the spectral characteristics of the image, approximately 34% "
            "of the total area is covered by the water body. The vegetated regions "
            "account for roughly 41% and built-up areas for approximately 18%. "
            "The remaining 7% includes bare soil and mixed transitional zones."
        ),
        "evidence": [
            {
                "claim": "Water coverage ~34% of total area",
                "evidence_type": EvidenceType.PIXEL_AREA,
                "confidence": 0.81,
            },
            {
                "claim": "Vegetation coverage ~41%",
                "evidence_type": EvidenceType.PIXEL_AREA,
                "confidence": 0.78,
            },
        ],
        "confidence": 0.79,
    },
    QueryIntent.OBJECT_IDENTIFICATION.value: {
        "answer": (
            "The following land-cover classes and objects are identified in the image: "
            "1) Water body (reservoir/lake) — central region; "
            "2) Dense broadleaf vegetation — north and east; "
            "3) Sparse scrubland — transitional zones; "
            "4) Residential/commercial built-up area — southwest; "
            "5) Road network — connecting settlement to main boundary."
        ),
        "evidence": [
            {
                "claim": "Water body — reservoir or lake",
                "bbox": [380, 280, 1150, 880],
                "evidence_type": EvidenceType.BBOX,
                "confidence": 0.87,
            },
            {
                "claim": "Dense broadleaf vegetation",
                "bbox": [900, 0, 1920, 600],
                "evidence_type": EvidenceType.BBOX,
                "confidence": 0.80,
            },
        ],
        "confidence": 0.82,
    },
    QueryIntent.BUILT_UP_ANALYSIS.value: {
        "answer": (
            "Built-up regions are primarily concentrated in the southwestern portion "
            "of the image. The settlement patterns indicate a mix of residential and "
            "small commercial structures. Road connectivity suggests planned development. "
            "The estimated built-up area covers approximately 18% of the total extent."
        ),
        "evidence": [
            {
                "claim": "Dense built-up region — southwest quadrant",
                "bbox": [0, 900, 600, 1440],
                "evidence_type": EvidenceType.BBOX,
                "confidence": 0.83,
            },
        ],
        "confidence": 0.81,
    },
    QueryIntent.WATER_ANALYSIS.value: {
        "answer": (
            "A significant water body is visible in the central-to-eastern area of "
            "the image. The spectral signature is consistent with open water (deep "
            "blue/near-black in NIR). The extent appears stable with no visible "
            "flooding of adjacent areas. Estimated surface area coverage: ~34%."
        ),
        "evidence": [
            {
                "claim": "Open water body — central region",
                "bbox": [380, 280, 1150, 880],
                "evidence_type": EvidenceType.BBOX,
                "confidence": 0.90,
            },
        ],
        "confidence": 0.86,
    },
}

_DEFAULT_FIXTURE = _FIXTURES[QueryIntent.SCENE_DESCRIPTION.value]


class MockSingleImageSpecialist(Specialist):
    """
    Mock single-image analysis specialist.
    Returns structured, intent-matched demo outputs.
    """

    @property
    def name(self) -> str:
        return "mock_single_image"

    @property
    def capabilities(self) -> list[str]:
        return [
            Capability.SINGLE_IMAGE_ANALYSIS,
            Capability.VQA,
            Capability.SCENE_DESCRIPTION,
            Capability.OBJECT_IDENTIFICATION,
            Capability.BUILT_UP_ANALYSIS,
            Capability.WATER_ANALYSIS,
        ]

    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        # Simulate realistic processing delay
        await asyncio.sleep(0.15)

        fixture = _FIXTURES.get(request.intent.value, _DEFAULT_FIXTURE)

        evidence_items = [
            Evidence(
                evidence_id=uuid.uuid4().hex,
                specialist=self.name,
                source="mock_vision_model",
                claim=e["claim"],
                evidence_type=e.get("evidence_type", EvidenceType.MODEL_PREDICTION),
                bbox=e.get("bbox"),
                confidence=e.get("confidence", 0.75),
            )
            for e in fixture["evidence"]
        ]

        return SpecialistResult(
            specialist=self.name,
            status=AnalysisStatus.SUCCESS,
            answer=fixture["answer"],
            evidence=evidence_items,
            raw_confidence=fixture["confidence"],
            metadata={
                "input_configuration": request.input_configuration.value,
                "intent": request.intent.value,
                "files_processed": len(request.file_ids),
                "provider": "mock",
            },
        )
