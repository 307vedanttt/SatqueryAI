"""
SatQuery AI — Mock Grounding Specialist

Simulates text-guided region grounding — returns bounding boxes
for named objects/regions in the query.
"""

import asyncio
import re
import uuid

from app.models.schemas import (
    AnalysisStatus,
    Evidence,
    EvidenceType,
    SpecialistRequest,
    SpecialistResult,
)
from app.registry.capabilities import Capability
from app.specialists.base import Specialist

# Simple keyword → bbox fixture map for demo
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
    @property
    def name(self) -> str:
        return "mock_grounding"

    @property
    def capabilities(self) -> list[str]:
        return [Capability.GROUNDING]

    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        await asyncio.sleep(0.12)

        query_lower = request.query.lower()

        # Find matching fixture
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
