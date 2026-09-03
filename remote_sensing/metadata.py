"""
remote_sensing/metadata.py — ImageMetadata validation and display utilities
"""

import logging
from schemas.contracts import ImageMetadata

logger = logging.getLogger(__name__)

_NO_CRS: str = "none"


def validate_metadata_complete(meta: ImageMetadata) -> tuple[bool, str]:
    """
    Validate that an ImageMetadata record is minimally complete for processing.

    Checks that required numeric fields are non-zero and required string fields
    are non-empty. Fields that may legitimately be absent for benchmark images
    (crs, resolution_m, acquisition_date) are NOT checked here — callers that
    need those fields should validate them separately (e.g., check_coregistration).

    Args:
        meta: The ImageMetadata record to validate.

    Returns:
        (True, "") if all required fields pass.
        (False, reason) with a human-readable explanation of the first failure.
    """
    if not meta.sensor or not meta.sensor.strip():
        return False, "sensor field is empty; must be 'optical', 'sar', or 'multispectral'."

    if not meta.file_path or not meta.file_path.strip():
        return False, "file_path field is empty; a valid file path is required."

    if meta.width <= 0:
        return False, f"width must be > 0 (got {meta.width})."

    if meta.height <= 0:
        return False, f"height must be > 0 (got {meta.height})."

    if meta.bands <= 0:
        return False, f"bands must be > 0 (got {meta.bands})."

    return True, ""


def summarize_metadata(meta: ImageMetadata) -> str:
    """
    Return a one-line human-readable summary of image metadata for logging and UI display.

    Example outputs:
        "Optical, 10980x10980px, 4 bands, 10m resolution, EPSG:4326"
        "SAR, 1000x1000px, 1 band, 0m resolution, no CRS (benchmark)"

    Args:
        meta: The ImageMetadata record to summarise.

    Returns:
        A single-line summary string.
    """
    sensor_label = meta.sensor.title()

    size_str = f"{meta.width}x{meta.height}px"

    bands_str = f"{meta.bands} band(s)"

    if meta.resolution_m > 0:
        res_str = f"{meta.resolution_m:.0f}m resolution"
    else:
        res_str = "no resolution (benchmark)"

    crs_raw = meta.crs or _NO_CRS
    if crs_raw.strip().lower() == _NO_CRS:
        crs_str = "no CRS (benchmark)"
    else:
        crs_str = crs_raw

    return f"{sensor_label}, {size_str}, {bands_str}, {res_str}, {crs_str}"
