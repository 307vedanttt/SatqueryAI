"""
SatQuery AI — Metadata Validation & Summarization (Person D - Part 1)
"""

from typing import Tuple
from schemas.contracts import ImageMetadata


def validate_metadata_complete(meta: ImageMetadata) -> Tuple[bool, str]:
    """Check that required ImageMetadata fields are populated with valid values."""
    if not meta.file_path:
        return False, "Missing file_path"
    if meta.width <= 0 or meta.height <= 0:
        return False, f"Invalid image dimensions: {meta.width}x{meta.height}"
    if meta.bands <= 0:
        return False, f"Invalid band count: {meta.bands}"
    if meta.resolution_m < 0:
        return False, f"Invalid negative resolution: {meta.resolution_m}"
    return True, "Metadata complete and valid"


def summarize_metadata(meta: ImageMetadata) -> str:
    """Produce a human-readable one-line summary of image metadata."""
    sensor_name = (meta.sensor or "Unknown").capitalize()
    return (
        f"{sensor_name}, {meta.width}x{meta.height}px, {meta.bands} band(s), "
        f"{meta.resolution_m}m resolution, {meta.crs}"
    )
