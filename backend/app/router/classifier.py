"""
SatQuery AI — Input Configuration Classifier

Classifies uploaded images into:
  SINGLE_OPTICAL  — one optical/multispectral image
  SINGLE_SAR      — one SAR image
  OPTICAL_SAR_PAIR — two images: one optical + one SAR
  BI_TEMPORAL     — two images of same type, different dates
  UNKNOWN         — cannot determine safely

Rules are DETERMINISTIC — not LLM-based.
The LLM may later assist as a secondary signal but never as sole authority.
"""

from app.core.logging import get_logger
from app.ingestion.alignment import validate_pair
from app.models.schemas import ImageMetadata, InputConfiguration

logger = get_logger(__name__)


def classify_input_configuration(images: list[ImageMetadata]) -> InputConfiguration:
    """
    Classify the uploaded image set into a known input configuration.
    
    Args:
        images: List of ImageMetadata for uploaded files.
    
    Returns:
        InputConfiguration enum value.
    """
    if not images:
        return InputConfiguration.UNKNOWN

    n = len(images)

    # --- Single image ---
    if n == 1:
        img = images[0]
        if img.image_type == "sar":
            return InputConfiguration.SINGLE_SAR
        return InputConfiguration.SINGLE_OPTICAL

    # --- Two images ---
    if n == 2:
        return _classify_pair(images[0], images[1])

    # --- More than two images ---
    # Not yet supported — return UNKNOWN
    logger.warning("unsupported_image_count", count=n)
    return InputConfiguration.UNKNOWN


def _classify_pair(img1: ImageMetadata, img2: ImageMetadata) -> InputConfiguration:
    """Classify a two-image input."""
    type1 = img1.image_type or "unknown"
    type2 = img2.image_type or "unknown"

    is_sar_1 = type1 == "sar"
    is_sar_2 = type2 == "sar"

    # Optical + SAR pair
    if is_sar_1 != is_sar_2:
        # One SAR, one optical — validate alignment
        validation = validate_pair(img1, img2)
        if not validation.valid:
            logger.warning(
                "pair_alignment_failed",
                error=validation.error_code,
                message=validation.message,
            )
            # Return UNKNOWN rather than guessing — let the caller surface this error
            return InputConfiguration.UNKNOWN
        return InputConfiguration.OPTICAL_SAR_PAIR

    # Both same type — check if bi-temporal (different dates)
    date1 = img1.acquisition_date
    date2 = img2.acquisition_date

    if date1 and date2 and date1 != date2:
        # Different acquisition dates → likely bi-temporal
        validation = validate_pair(img1, img2)
        if validation.valid:
            return InputConfiguration.BI_TEMPORAL
        else:
            logger.warning("bitemporal_alignment_failed", error=validation.error_code)
            return InputConfiguration.UNKNOWN

    # Both optical, no date metadata to distinguish → treat as bi-temporal if aligned
    if not is_sar_1 and not is_sar_2:
        if img1.is_geotiff and img2.is_geotiff:
            validation = validate_pair(img1, img2)
            if validation.valid:
                # No dates available — assume bi-temporal (user intent)
                return InputConfiguration.BI_TEMPORAL

    return InputConfiguration.UNKNOWN
