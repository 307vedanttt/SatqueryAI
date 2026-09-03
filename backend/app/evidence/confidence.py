"""
SatQuery AI — Confidence Calculator

Computes final confidence using a weighted formula across four components.
The formula is configurable via environment variables.

Formula (provisional — must not be presented as scientifically validated):

  final = w_input  * input_score
        + w_spec   * specialist_score
        + w_evid   * evidence_score
        + w_agree  * agreement_score

Defaults:
  w_input  = 0.20
  w_spec   = 0.40
  w_evid   = 0.20
  w_agree  = 0.20

The final score is clamped to [0.0, 1.0].
"""

from app.core.config import Settings
from app.models.schemas import (
    ConfidenceBreakdown,
    ConfidenceLabel,
    DisagreementResult,
    Evidence,
    InputConfiguration,
    SpecialistResult,
)


class ConfidenceCalculator:
    """
    Computes a structured confidence breakdown.
    Uses configurable weights from Settings.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def calculate(
        self,
        input_config: InputConfiguration,
        specialist_results: list[SpecialistResult],
        evidence: list[Evidence],
        disagreement: DisagreementResult,
    ) -> ConfidenceBreakdown:
        """Compute final confidence breakdown."""
        input_score = self._input_score(input_config)
        specialist_score = self._specialist_score(specialist_results)
        evidence_score = self._evidence_score(evidence)
        agreement_score = self._agreement_score(disagreement)

        s = self._settings
        final = (
            s.CONFIDENCE_WEIGHT_INPUT * input_score
            + s.CONFIDENCE_WEIGHT_SPECIALIST * specialist_score
            + s.CONFIDENCE_WEIGHT_EVIDENCE * evidence_score
            + s.CONFIDENCE_WEIGHT_AGREEMENT * agreement_score
        )
        final = max(0.0, min(1.0, final))

        label = self._label(final)
        explanation = self._explain(final, label, disagreement, evidence)

        return ConfidenceBreakdown(
            input_score=input_score,
            specialist_score=specialist_score,
            evidence_score=evidence_score,
            agreement_score=agreement_score,
            final_score=round(final, 3),
            label=label,
            explanation=explanation,
        )

    # ------------------------------------------------------------------ #

    def _input_score(self, config: InputConfiguration) -> float:
        """Score based on how well-defined the input configuration is."""
        if config == InputConfiguration.UNKNOWN:
            return 0.20
        return 0.90

    def _specialist_score(self, results: list[SpecialistResult]) -> float:
        """Average of specialist raw_confidence values."""
        if not results:
            return 0.0
        return sum(r.raw_confidence for r in results) / len(results)

    def _evidence_score(self, evidence: list[Evidence]) -> float:
        """Score based on evidence quantity and average confidence."""
        if not evidence:
            return 0.10
        avg_conf = sum(e.confidence for e in evidence) / len(evidence)
        # Bonus for having multiple evidence items (up to 5)
        quantity_bonus = min(1.0, len(evidence) / 5) * 0.15
        return min(1.0, avg_conf + quantity_bonus)

    def _agreement_score(self, disagreement: DisagreementResult) -> float:
        """Score based on inter-specialist agreement."""
        if not disagreement.detected:
            return 1.0
        # Penalize based on number of disagreeing items
        penalty = min(0.60, len(disagreement.items) * 0.15)
        return max(0.20, 1.0 - penalty)

    def _label(self, score: float) -> ConfidenceLabel:
        if score >= self._settings.CONFIDENCE_THRESHOLD_HIGH:
            return ConfidenceLabel.HIGH
        elif score >= self._settings.CONFIDENCE_THRESHOLD_LOW:
            return ConfidenceLabel.MEDIUM
        elif score > 0.20:
            return ConfidenceLabel.LOW
        return ConfidenceLabel.INSUFFICIENT

    def _explain(
        self,
        score: float,
        label: ConfidenceLabel,
        disagreement: DisagreementResult,
        evidence: list[Evidence],
    ) -> str:
        parts: list[str] = []

        if label == ConfidenceLabel.HIGH:
            parts.append("High confidence: the input was valid and specialist outputs were consistent.")
        elif label == ConfidenceLabel.MEDIUM:
            parts.append("Medium confidence: the analysis is reasonably well-supported but some uncertainty exists.")
        elif label == ConfidenceLabel.LOW:
            parts.append("Low confidence: the specialist outputs have limited support from evidence.")
        else:
            parts.append("Insufficient confidence to provide a reliable answer.")

        if disagreement.detected:
            parts.append(
                f"Note: {len(disagreement.items)} conflicting claims were detected across specialist outputs."
            )

        if not evidence:
            parts.append("No structured evidence was extracted.")
        elif len(evidence) < 2:
            parts.append("Limited evidence was available to support the conclusion.")

        return " ".join(parts)
