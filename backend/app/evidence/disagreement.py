"""
SatQuery AI — Disagreement Detector

Compares claims across specialist results to detect contradictions.
If detected, surfaces them for explicit communication to the user.

Do NOT silently choose one claim when specialists disagree.
"""

from app.models.schemas import DisagreementItem, DisagreementResult, SpecialistResult

# Keywords that signal opposing claims
_CONTRADICTION_PAIRS: list[tuple[frozenset[str], frozenset[str]]] = [
    (frozenset(["bare soil", "bare", "open soil"]), frozenset(["built", "building", "urban", "structure"])),
    (frozenset(["water", "flood", "inundation"]), frozenset(["dry", "bare", "vegetation"])),
    (frozenset(["dense vegetation", "forest", "trees"]), frozenset(["deforested", "cleared", "bare"])),
    (frozenset(["no change", "stable"]), frozenset(["change", "changed", "new", "appeared", "loss"])),
]


class DisagreementDetector:
    """
    Detects conflicting claims across multiple specialist results.
    
    For multimodal analysis (optical+SAR, or multi-model),
    it compares the evidence claims from each source.
    """

    def detect(self, specialist_results: list[SpecialistResult]) -> DisagreementResult:
        """
        Detect disagreements across specialist results.
        
        Strategy:
        1. Collect claims per source (sensor / specialist)
        2. Compare claim pairs for semantic contradiction using keyword rules
        3. Flag contradictions as DisagreementItems
        """
        if len(specialist_results) == 0:
            return DisagreementResult(detected=False)

        # Collect all (source, description) pairs
        source_claims: list[tuple[str, str, float]] = []
        for result in specialist_results:
            for ev in result.evidence:
                source_claims.append((ev.source, ev.description.lower(), ev.confidence))

        # Within optical+SAR results, also check cross-sensor evidence
        all_items: list[DisagreementItem] = []

        for i, (src_a, claim_a, conf_a) in enumerate(source_claims):
            for j, (src_b, claim_b, conf_b) in enumerate(source_claims):
                if i >= j or src_a == src_b:
                    continue
                if _claims_contradict(claim_a, claim_b):
                    all_items.append(DisagreementItem(source=src_a, claim=claim_a[:120], confidence=conf_a))
                    all_items.append(DisagreementItem(source=src_b, claim=claim_b[:120], confidence=conf_b))

        # Deduplicate items
        seen = set()
        unique_items: list[DisagreementItem] = []
        for item in all_items:
            key = f"{item.source}|{item.claim[:40]}"
            if key not in seen:
                seen.add(key)
                unique_items.append(item)

        if unique_items:
            explanation = (
                f"Conflicting claims were detected between {len(unique_items)} evidence sources. "
                "The final answer reflects this uncertainty — field verification may be required."
            )
            return DisagreementResult(detected=True, items=unique_items, explanation=explanation)

        return DisagreementResult(detected=False)


def _claims_contradict(claim_a: str, claim_b: str) -> bool:
    """Return True if the two claims appear semantically contradictory."""
    for set_a, set_b in _CONTRADICTION_PAIRS:
        a_matches = any(kw in claim_a for kw in set_a)
        b_matches = any(kw in claim_b for kw in set_b)
        if a_matches and b_matches:
            return True
        # Also check reversed
        b_matches_a = any(kw in claim_b for kw in set_a)
        a_matches_b = any(kw in claim_a for kw in set_b)
        if b_matches_a and a_matches_b:
            return True
    return False
