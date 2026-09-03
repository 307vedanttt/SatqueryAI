"""
SatQuery AI — Mock Optical+SAR Specialist

Simulates fusion analysis of an optical + SAR image pair.
Intentionally produces a mild disagreement scenario to test
the disagreement detection and reporting pipeline.
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


class MockOpticalSARSpecialist(Specialist):
    @property
    def name(self) -> str:
        return "mock_optical_sar"

    @property
    def capabilities(self) -> list[str]:
        return [
            Capability.OPTICAL_SAR_FUSION,
            Capability.BUILT_UP_ANALYSIS,
            Capability.WATER_ANALYSIS,
        ]

    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        await asyncio.sleep(0.20)

        answer = (
            "Optical analysis reveals a region with moderate spectral reflectance "
            "consistent with mixed built-up and bare-soil areas in the northern sector. "
            "The SAR backscatter analysis of the same region indicates strong double-bounce "
            "returns typical of dense urban structures, suggesting built-up area. "
            "The water body in the central region is confirmed by both sensors — "
            "low optical reflectance and very low SAR backscatter (specular reflection). "
            "\n\n"
            "Note: The optical sensor suggests the northern sector may include bare soil, "
            "while SAR strongly indicates built-up structures. This disagreement is flagged "
            "for your attention — field verification is recommended for the northern region."
        )

        evidence_items = [
            Evidence(
                evidence_id=uuid.uuid4().hex,
                specialist=self.name,
                source="optical_channel",
                claim="Northern sector: possible bare soil (low NDVI, moderate reflectance)",
                evidence_type=EvidenceType.SENSOR_COMPARISON,
                bbox=[0, 0, 1920, 480],
                confidence=0.71,
                metadata={"sensor": "optical"},
            ),
            Evidence(
                evidence_id=uuid.uuid4().hex,
                specialist=self.name,
                source="sar_channel",
                claim="Northern sector: strong double-bounce consistent with built-up area",
                evidence_type=EvidenceType.SENSOR_COMPARISON,
                bbox=[0, 0, 1920, 480],
                confidence=0.78,
                metadata={"sensor": "sar"},
            ),
            Evidence(
                evidence_id=uuid.uuid4().hex,
                specialist=self.name,
                source="fusion",
                claim="Central water body confirmed by both sensors",
                evidence_type=EvidenceType.BBOX,
                bbox=[380, 280, 1150, 880],
                confidence=0.91,
                metadata={"sensor": "optical+sar"},
            ),
        ]

        return SpecialistResult(
            specialist=self.name,
            status=AnalysisStatus.SUCCESS,
            answer=answer,
            evidence=evidence_items,
            raw_confidence=0.74,
            metadata={
                "input_configuration": request.input_configuration.value,
                "intent": request.intent.value,
                "disagreement_flagged": True,
                "provider": "mock",
            },
        )
