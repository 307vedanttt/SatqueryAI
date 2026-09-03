"""
SatQuery AI — Mock Change Detection Specialist

Simulates bi-temporal change detection analysis.
Returns structured change evidence with spatial regions.
"""

import asyncio
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


class MockChangeDetectionSpecialist(Specialist):
    @property
    def name(self) -> str:
        return "mock_change_detection"

    @property
    def capabilities(self) -> list[str]:
        return [Capability.CHANGE_DETECTION, Capability.CHANGE_VQA]

    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        await asyncio.sleep(0.18)

        # Determine date labels if available
        meta = request.metadata
        date1 = meta[0].acquisition_date if meta else "T1"
        date2 = meta[1].acquisition_date if len(meta) > 1 else "T2"
        d1 = date1 or "earlier image"
        d2 = date2 or "later image"

        answer = (
            f"Comparing {d1} to {d2}, the following changes are detected:\n\n"
            "1. **Built-up area expansion (northwest):** New rectangular structures "
            "have appeared in the northwestern quadrant, indicating residential or "
            "commercial development. Estimated expansion: ~2.4 km².\n\n"
            "2. **Vegetation loss (eastern sector):** Dense tree cover visible in "
            "the earlier image has been partially cleared in the later image. "
            "Affected area: ~1.1 km².\n\n"
            "3. **Water body extent change (central):** The water body boundary has "
            "shifted slightly southward, suggesting seasonal fluctuation or drawdown. "
            "Net change: minor reduction (~0.3 km²).\n\n"
            "No significant change detected in the southern agricultural zone."
        )

        evidence_items = [
            Evidence(
                evidence_id=uuid.uuid4().hex,
                specialist=self.name,
                source="temporal_differencing",
                claim="New built-up structures appeared in northwestern quadrant",
                evidence_type=EvidenceType.TEMPORAL_DIFFERENCE,
                bbox=[0, 0, 640, 540],
                date=d2,
                confidence=0.85,
            ),
            Evidence(
                evidence_id=uuid.uuid4().hex,
                specialist=self.name,
                source="temporal_differencing",
                claim="Vegetation loss detected in eastern sector",
                evidence_type=EvidenceType.TEMPORAL_DIFFERENCE,
                bbox=[1200, 200, 1920, 900],
                date=d2,
                confidence=0.79,
            ),
            Evidence(
                evidence_id=uuid.uuid4().hex,
                specialist=self.name,
                source="temporal_differencing",
                claim="Minor reduction in water body extent",
                evidence_type=EvidenceType.TEMPORAL_DIFFERENCE,
                bbox=[380, 280, 1150, 880],
                date=d2,
                confidence=0.74,
            ),
        ]

        return SpecialistResult(
            specialist=self.name,
            status=AnalysisStatus.SUCCESS,
            answer=answer,
            evidence=evidence_items,
            raw_confidence=0.81,
            metadata={
                "input_configuration": request.input_configuration.value,
                "intent": request.intent.value,
                "date_1": d1,
                "date_2": d2,
                "change_count": 3,
                "provider": "mock",
            },
        )
