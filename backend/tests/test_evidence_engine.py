import pytest
from app.evidence.service import EvidenceSynthesisService
from app.models.schemas import SpecialistResult, Evidence, EvidenceType, InputConfiguration

@pytest.fixture
def service():
    return EvidenceSynthesisService()

def test_strong_evidence(service):
    # High specialist confidence, good evidence, no disagreement
    ev = Evidence(
        source="sensor_a",
        type=EvidenceType.REGION,
        description="Clear building footprint",
        confidence=0.95
    )
    res = SpecialistResult(
        specialist="mock_single",
        status="success",
        answer="I see a building",
        raw_confidence=0.90,
        evidence=[ev]
    )
    result = service.synthesize(InputConfiguration.SINGLE_OPTICAL, [res])
    
    assert not result.failsafe.is_insufficient
    assert result.confidence.final_score > 0.7
    assert len(result.evidence) == 1
    assert not result.disagreement.detected

def test_weak_evidence(service):
    # Low confidence evidence, but just enough to pass threshold maybe
    ev = Evidence(
        source="sensor_a",
        type=EvidenceType.REGION,
        description="Faint outline",
        confidence=0.30
    )
    res = SpecialistResult(
        specialist="mock_single",
        status="success",
        answer="Might be a building",
        raw_confidence=0.40,
        evidence=[ev]
    )
    result = service.synthesize(InputConfiguration.SINGLE_OPTICAL, [res])
    
    # Depending on weights, this might trigger fail-safe or just be LOW confidence
    # But it shouldn't fail validation
    assert result.confidence.final_score < 0.6

def test_missing_evidence(service):
    res = SpecialistResult(
        specialist="mock_single",
        status="success",
        answer="I think it's a building but I have no evidence",
        raw_confidence=0.80,
        evidence=[]
    )
    result = service.synthesize(InputConfiguration.SINGLE_OPTICAL, [res])
    
    assert result.failsafe.is_insufficient
    assert "No structured evidence" in result.failsafe.reason
    assert result.confidence.evidence_score <= 0.1

def test_conflicting_outputs(service):
    # Water vs Dry/Bare
    ev1 = Evidence(
        source="optical",
        type=EvidenceType.MODEL_PREDICTION,
        description="The area is completely dry and bare soil.",
        confidence=0.85
    )
    res1 = SpecialistResult(
        specialist="mock_opt",
        status="success",
        answer="Dry land.",
        raw_confidence=0.85,
        evidence=[ev1]
    )
    
    ev2 = Evidence(
        source="sar",
        type=EvidenceType.MODEL_PREDICTION,
        description="High inundation, deep water detected.",
        confidence=0.90
    )
    res2 = SpecialistResult(
        specialist="mock_sar",
        status="success",
        answer="Flood.",
        raw_confidence=0.90,
        evidence=[ev2]
    )
    
    result = service.synthesize(InputConfiguration.OPTICAL_SAR_PAIR, [res1, res2])
    
    assert result.disagreement.detected
    assert len(result.disagreement.items) == 2
    # Disagreement penalty should lower the confidence
    assert result.confidence.agreement_score < 1.0

def test_low_confidence_specialist(service):
    ev = Evidence(
        source="sensor",
        description="Not sure",
        confidence=0.1
    )
    res = SpecialistResult(
        specialist="mock",
        status="success",
        answer="I do not know",
        raw_confidence=0.10,
        evidence=[ev]
    )
    result = service.synthesize(InputConfiguration.SINGLE_OPTICAL, [res])
    
    assert result.failsafe.is_insufficient
    assert "confidence is too low" in result.failsafe.recommended_action

def test_invalid_confidence_values(service):
    res = SpecialistResult(
        specialist="mock",
        status="success",
        answer="Invalid conf",
        raw_confidence=1.5,
        evidence=[]
    )
    with pytest.raises(ValueError, match="Invalid confidence value"):
        service.synthesize(InputConfiguration.SINGLE_OPTICAL, [res])
        
    ev = Evidence(
        source="sensor",
        description="Valid result conf, invalid ev conf",
        confidence=-0.1
    )
    res2 = SpecialistResult(
        specialist="mock",
        status="success",
        answer="Invalid ev conf",
        raw_confidence=0.8,
        evidence=[ev]
    )
    with pytest.raises(ValueError, match="Invalid confidence value"):
        service.synthesize(InputConfiguration.SINGLE_OPTICAL, [res2])
