"""
SatQuery AI — Change Detection Specialist Head (Person C)

Executes bi-temporal change detection and change-VQA.
"""

import logging
from PIL import Image
from schemas.contracts import SpecialistRequest, SpecialistResponse
from models.change.encoder import SiameseEncoder
from models.change.difference import ChangeEnhancement, compute_change_magnitude

logger = logging.getLogger("satquery.models.change.change_head")

_SIAMESE_ENCODER = None
_CHANGE_ENHANCEMENT = None


def _get_change_modules():
    global _SIAMESE_ENCODER, _CHANGE_ENHANCEMENT
    if _SIAMESE_ENCODER is None:
        _SIAMESE_ENCODER = SiameseEncoder()
        _CHANGE_ENHANCEMENT = ChangeEnhancement()
        _SIAMESE_ENCODER.eval()
        _CHANGE_ENHANCEMENT.eval()
    return _SIAMESE_ENCODER, _CHANGE_ENHANCEMENT


def run_change_detection(request: SpecialistRequest) -> SpecialistResponse:
    """Execute bi-temporal change detection or change-VQA."""
    if len(request.images) != 2:
        return SpecialistResponse(
            task="change_detection",
            answer="Error: Change detection requires exactly 2 images.",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=f"Change detection requires exactly 2 images, got {len(request.images)}",
        )

    p1 = request.images[0].file_path
    p2 = request.images[1].file_path

    try:
        img1 = Image.open(p1).convert("RGB")
        img2 = Image.open(p2).convert("RGB")
    except Exception as e:
        return SpecialistResponse(
            task="change_detection",
            answer=f"Error loading bi-temporal image pair: {e}",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=str(e),
        )

    try:
        encoder, enhancement = _get_change_modules()

        t1 = encoder.preprocess_image(img1)
        t2 = encoder.preprocess_image(img2)

        f1, f2 = encoder(t1, t2)
        change_feat = enhancement(f1, f2)
        magnitude = compute_change_magnitude(f1, f2)

        # Categorize magnitude
        if magnitude > 0.40:
            change_desc = f"Significant bi-temporal change detected (magnitude: {magnitude:.2f}). Major structural or land cover alterations observed between dates."
            conf_tier = "high"
            conf_score = 0.88
        elif magnitude > 0.15:
            change_desc = f"Moderate bi-temporal change detected (magnitude: {magnitude:.2f}). Minor surface modifications observed."
            conf_tier = "moderate"
            conf_score = 0.72
        else:
            change_desc = f"Minimal/no significant bi-temporal change detected (magnitude: {magnitude:.2f}). Land cover remains stable across acquisition dates."
            conf_tier = "high"
            conf_score = 0.85

        # Check if change-VQA vs change_detection
        is_vqa = ("?" in request.query) or any(w in request.query.lower() for w in ["what", "where", "has", "how"])
        task_name = "change_vqa" if is_vqa else "change_detection"

        answer_text = (
            f"Bi-Temporal Change Analysis for query '{request.query}':\n"
            f"{change_desc}\n"
            f"Signal evidence: Computed feature difference tensor shape {list(change_feat.shape)}."
        )

        return SpecialistResponse(
            task=task_name,
            answer=answer_text,
            confidence=conf_score,
            confidence_tier=conf_tier,
            bounding_boxes=[],
            evidence=[
                f"Siamese feature difference magnitude: {magnitude:.4f}",
                f"Image 1 CRS: {request.images[0].crs}, Image 2 CRS: {request.images[1].crs}",
            ],
            model_used="Siamese ResNet18 encoder + Difference module + Heuristic phrasing",
            status="success",
        )

    except Exception as e:
        logger.error(f"Change detection exception: {e}")
        return SpecialistResponse(
            task="change_detection",
            answer=f"Change detection error: {e}",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=str(e),
        )
