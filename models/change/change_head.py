"""
Main change detection logic.
"""
import logging
from schemas.contracts import SpecialistRequest, SpecialistResponse
from models.change.encoder import SiameseEncoder
from models.change.difference import compute_change_magnitude

logger = logging.getLogger(__name__)

# Module-level singleton
_encoder = None

def run_change_detection(request: SpecialistRequest) -> SpecialistResponse:
    """
    Runs change detection on two images provided in the request.
    """
    global _encoder
    
    if len(request.images) != 2:
        return SpecialistResponse(
            task=request.task_hint if request.task_hint else "change_detection",
            answer="Error: Exactly 2 images are required.",
            confidence=0.0,
            confidence_tier="low",
            bounding_boxes=[],
            evidence=[],
            model_used="Siamese ResNet18 encoder + absolute difference module",
            status="error",
            error_message="Exactly 2 images are required."
        )
        
    try:
        img1_path = request.images[0].file_path
        img2_path = request.images[1].file_path
        
        img1_tensor = SiameseEncoder.preprocess_image(img1_path)
        img2_tensor = SiameseEncoder.preprocess_image(img2_path)
        
        if _encoder is None:
            _encoder = SiameseEncoder()
            _encoder.eval()
            
        f1, f2 = _encoder(img1_tensor, img2_tensor)
        
        magnitude = compute_change_magnitude(f1, f2)
        
        if magnitude > 0.4:
            answer = f"Significant change detected between the two images. The feature-level analysis indicates substantial differences in land cover or surface characteristics. The change magnitude signal is {magnitude:.2f} (scale 0–1), suggesting notable transformation."
        elif 0.15 < magnitude <= 0.4:
            answer = f"Moderate change detected between the two images (change magnitude: {magnitude:.2f}). Some differences are present but the extent of change is limited. Region-specific analysis is recommended for precise characterization."
        else:
            answer = f"Minimal change detected between the two images (change magnitude: {magnitude:.2f}). The two images appear largely similar in their feature representation. Seasonal variations or imaging conditions may account for minor differences."
            
        if request.task_hint == "change_vqa":
            answer += f"\n\nRegarding your question '{request.query}': Based on the computed change signal ({magnitude:.2f}), "
            if magnitude > 0.4:
                answer += "there is clear evidence of modification."
            else:
                answer += "there is minimal evidence of modification."
                
        if abs(magnitude - 0.4) > 0.2:
            confidence_tier = "high"
        else:
            confidence_tier = "moderate"
            
        return SpecialistResponse(
            task=request.task_hint if request.task_hint else "change_detection",
            answer=answer,
            confidence=float(magnitude),
            confidence_tier=confidence_tier,
            bounding_boxes=[],
            evidence=[],
            model_used="Siamese ResNet18 encoder + absolute difference module",
            status="success",
            error_message=None
        )
        
    except Exception as e:
        logger.exception("Error in change detection")
        return SpecialistResponse(
            task=request.task_hint if request.task_hint else "change_detection",
            answer=f"Error occurred: {str(e)}",
            confidence=0.0,
            confidence_tier="low",
            bounding_boxes=[],
            evidence=[],
            model_used="Siamese ResNet18 encoder + absolute difference module",
            status="error",
            error_message=str(e)
        )
