"""
SatQuery AI — Evidence Collector

Collects raw evidence items from specialist results
before they are passed to the synthesizer.
Provides filtering and type-based retrieval.
"""

from app.models.schemas import Evidence, EvidenceType, SpecialistResult


class EvidenceCollector:
    """
    Collects and provides access to evidence from specialist results.
    """

    def __init__(self) -> None:
        self._items: list[Evidence] = []

    def collect(self, results: list[SpecialistResult]) -> None:
        """Collect all evidence from a list of specialist results."""
        for result in results:
            self._items.extend(result.evidence)

    def get_all(self) -> list[Evidence]:
        return list(self._items)

    def get_by_type(self, evidence_type: EvidenceType) -> list[Evidence]:
        return [e for e in self._items if e.evidence_type == evidence_type]

    def get_by_source(self, source: str) -> list[Evidence]:
        return [e for e in self._items if e.source == source]

    def get_bboxes(self) -> list[Evidence]:
        return [e for e in self._items if e.bbox is not None]

    def high_confidence(self, threshold: float = 0.75) -> list[Evidence]:
        return [e for e in self._items if e.confidence >= threshold]

    def clear(self) -> None:
        self._items.clear()
