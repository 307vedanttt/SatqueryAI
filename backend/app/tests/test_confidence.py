"""
SatQuery AI — Backend Tests: Confidence

Tests for confidence calculation, labels, disagreement detection,
and fail-safe behavior.
"""

import pytest

from app.core.config import get_settings
from app.evidence.confidence import ConfidenceCalculator
from app.evidence.disagreement import DisagreementDetector, _claims_contradict
from app.models.schemas import (
    AnalysisStatus,
    ConfidenceLabel,
    DisagreementResult,
    Evidence,
    EvidenceType,
    InputConfiguration,
    SpecialistResult,
)


def _make_result(confidence=0.85, claims=None) -> SpecialistResult:
    evidence = []
    for claim in (claims or ["Central water body identified"]):
        evidence.append(
            Evidence(
                specialist="test",
                source="optical",
                claim=claim,
                evidence_type=EvidenceType.BBOX,
                bbox=[100, 100, 500, 500],
                confidence=confidence,
            )
        )
    return SpecialistResult(
        specialist="test",
        status=AnalysisStatus.SUCCESS,
        answer="Test answer",
        evidence=evidence,
        raw_confidence=confidence,
    )


class TestConfidenceCalculator:
    @pytest.fixture
    def calc(self):
        return ConfidenceCalculator(get_settings())

    def test_high_confidence_single_image(self, calc):
        result = _make_result(0.90)
        no_disagreement = DisagreementResult(detected=False)
        evidence = result.evidence
        conf = calc.calculate(
            input_config=InputConfiguration.SINGLE_OPTICAL,
            specialist_results=[result],
            evidence=evidence,
            disagreement=no_disagreement,
        )
        assert conf.label == ConfidenceLabel.HIGH
        assert conf.final_score >= 0.75

    def test_low_confidence_unknown_config(self, calc):
        result = _make_result(0.30)
        no_disagreement = DisagreementResult(detected=False)
        conf = calc.calculate(
            input_config=InputConfiguration.UNKNOWN,
            specialist_results=[result],
            evidence=[],
            disagreement=no_disagreement,
        )
        assert conf.label in (ConfidenceLabel.LOW, ConfidenceLabel.MEDIUM, ConfidenceLabel.INSUFFICIENT)
        assert conf.final_score < 0.75

    def test_disagreement_reduces_confidence(self, calc):
        result = _make_result(0.80)
        disagreement = DisagreementResult(
            detected=True,
            items=[
                {"source": "optical", "claim": "bare soil", "confidence": 0.7},
                {"source": "sar", "claim": "built-up area", "confidence": 0.75},
            ],
        )
        conf_no_disagreement = calc.calculate(
            input_config=InputConfiguration.OPTICAL_SAR_PAIR,
            specialist_results=[result],
            evidence=result.evidence,
            disagreement=DisagreementResult(detected=False),
        )
        conf_with_disagreement = calc.calculate(
            input_config=InputConfiguration.OPTICAL_SAR_PAIR,
            specialist_results=[result],
            evidence=result.evidence,
            disagreement=DisagreementResult(detected=True, items=[]),
        )
        assert conf_with_disagreement.final_score <= conf_no_disagreement.final_score

    def test_confidence_score_clamped_to_range(self, calc):
        result = _make_result(1.0)
        conf = calc.calculate(
            input_config=InputConfiguration.SINGLE_OPTICAL,
            specialist_results=[result],
            evidence=result.evidence,
            disagreement=DisagreementResult(detected=False),
        )
        assert 0.0 <= conf.final_score <= 1.0

    def test_no_evidence_reduces_score(self, calc):
        result = _make_result(0.90)
        result.evidence = []
        conf_with = calc.calculate(
            input_config=InputConfiguration.SINGLE_OPTICAL,
            specialist_results=[result],
            evidence=result.evidence,
            disagreement=DisagreementResult(detected=False),
        )
        # No evidence should produce lower score than with evidence
        assert conf_with.evidence_score < 0.5

    def test_explanation_is_non_empty(self, calc):
        result = _make_result(0.85)
        conf = calc.calculate(
            input_config=InputConfiguration.SINGLE_OPTICAL,
            specialist_results=[result],
            evidence=result.evidence,
            disagreement=DisagreementResult(detected=False),
        )
        assert conf.explanation
        assert len(conf.explanation) > 10


class TestDisagreementDetector:
    def test_no_disagreement_single_specialist(self):
        result = _make_result(0.85, ["Central water body identified"])
        detector = DisagreementDetector()
        d = detector.detect([result])
        assert d.detected is False

    def test_claims_contradict_bare_soil_vs_built_up(self):
        assert _claims_contradict("possible bare soil area", "built-up urban structures") is True

    def test_claims_agree(self):
        assert _claims_contradict("water body present", "open water confirmed") is False

    def test_optical_sar_disagreement_detected(self):
        r1 = SpecialistResult(
            specialist="optical",
            status=AnalysisStatus.SUCCESS,
            answer="Bare soil",
            evidence=[
                Evidence(
                    specialist="optical", source="optical",
                    claim="possible bare soil area",
                    evidence_type=EvidenceType.REGION,
                    confidence=0.70,
                )
            ],
            raw_confidence=0.70,
        )
        r2 = SpecialistResult(
            specialist="sar",
            status=AnalysisStatus.SUCCESS,
            answer="Built-up",
            evidence=[
                Evidence(
                    specialist="sar", source="sar",
                    claim="strong double-bounce from built-up structures",
                    evidence_type=EvidenceType.REGION,
                    confidence=0.78,
                )
            ],
            raw_confidence=0.78,
        )
        detector = DisagreementDetector()
        d = detector.detect([r1, r2])
        assert d.detected is True
        assert len(d.items) >= 2
