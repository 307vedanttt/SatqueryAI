"""
SatQuery AI — Evidence Synthesizer

Aggregates evidence from one or more specialist results
into a unified, deduplicated evidence list.
"""

from app.models.schemas import Evidence, SpecialistResult


class EvidenceSynthesizer:
    """
    Combines evidence from multiple specialist results.
    Deduplicates by (claim, bbox) pairs.
    Orders evidence by descending confidence.
    """

    def synthesize(self, specialist_results: list[SpecialistResult]) -> list[Evidence]:
        """
        Aggregate all evidence from all specialist results.
        
        Args:
            specialist_results: Results from one or more specialists.
        
        Returns:
            Unified, sorted, deduplicated evidence list.
        """
        all_evidence: list[Evidence] = []
        seen_keys: set[str] = set()

        for result in specialist_results:
            for ev in result.evidence:
                # Deduplication key: claim text (first 80 chars) + bbox
                bbox_str = str(ev.bbox) if ev.bbox else "none"
                key = f"{ev.claim[:80]}|{bbox_str}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_evidence.append(ev)

        # Sort by confidence descending
        all_evidence.sort(key=lambda e: e.confidence, reverse=True)

        return all_evidence
