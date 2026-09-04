from pydantic import BaseModel
from typing import Any
from app.models.schemas import SpecialistResult, Evidence, DisagreementResult, ConfidenceBreakdown, InputConfiguration
from app.evidence.synthesizer import EvidenceSynthesizer
from app.evidence.disagreement import DisagreementDetector
from app.evidence.confidence import ConfidenceCalculator
from app.core.config import get_settings

class FailSafeResult(BaseModel):
    is_insufficient: bool
    reason: str | None = None
    recommended_action: str | None = None

class GroundedResult(BaseModel):
    evidence: list[Evidence]
    disagreement: DisagreementResult
    confidence: ConfidenceBreakdown
    failsafe: FailSafeResult

class EvidenceSynthesisService:
    """
    Centralized Evidence and Confidence Engine.
    Coordinates evidence deduplication, confidence calculation, disagreement detection,
    and applies fail-safe constraints to ensure evidence is never fabricated.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.synthesizer = EvidenceSynthesizer()
        self.detector = DisagreementDetector()
        self.calculator = ConfidenceCalculator(self.settings)

    def synthesize(
        self,
        input_config: InputConfiguration,
        specialist_results: list[SpecialistResult]
    ) -> GroundedResult:
        """
        Receives outputs from specialist models and creates a grounded result.
        """
        # Validate specialist confidences to catch malformed mock/model results
        for sr in specialist_results:
            if sr.raw_confidence < 0.0 or sr.raw_confidence > 1.0:
                raise ValueError(f"Invalid confidence value {sr.raw_confidence} from specialist {sr.specialist}. Must be [0.0, 1.0].")
            for ev in sr.evidence:
                if ev.confidence < 0.0 or ev.confidence > 1.0:
                    raise ValueError(f"Invalid confidence value {ev.confidence} in evidence. Must be [0.0, 1.0].")

        # 1. Synthesize Evidence
        unified_evidence = self.synthesizer.synthesize(specialist_results)
        
        # 2. Detect Disagreement
        disagreement = self.detector.detect(specialist_results)
        
        # 3. Calculate Transparent Confidence
        confidence = self.calculator.calculate(
            input_config=input_config,
            specialist_results=specialist_results,
            evidence=unified_evidence,
            disagreement=disagreement
        )
        
        # 4. Fail-Safe Checks
        is_insufficient = False
        reason = None
        recommended_action = None
        
        if not unified_evidence:
            is_insufficient = True
            reason = "No structured evidence was extracted by the specialist models."
            recommended_action = "Please provide an image with clearer features or try a broader query."
        elif confidence.final_score < self.settings.CONFIDENCE_THRESHOLD_LOW:
            is_insufficient = True
            reason = confidence.explanation
            if disagreement.detected:
                recommended_action = "Specialists strongly disagreed. Human validation is recommended."
            else:
                recommended_action = "The model's confidence is too low. Try zooming in or providing higher-resolution imagery."
                
        failsafe = FailSafeResult(
            is_insufficient=is_insufficient,
            reason=reason,
            recommended_action=recommended_action
        )
        
        return GroundedResult(
            evidence=unified_evidence,
            disagreement=disagreement,
            confidence=confidence,
            failsafe=failsafe
        )
