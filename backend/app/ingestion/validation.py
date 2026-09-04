"""
SatQuery AI — Imagery Validation Service

Validates single or paired imagery for configuration compatibility.
"""
from typing import Any, List, Optional
from pydantic import BaseModel
from app.models.schemas import ImageMetadata

class PairValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []

class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = []
    metadata: List[ImageMetadata] = []
    sensor_type: str = "unknown"
    confidence: float = 0.0
    source: str = "insufficient_metadata"
    pair_validation: Optional[PairValidationResult] = None

def check_overlap(bounds1: tuple[float, float, float, float] | None, bounds2: tuple[float, float, float, float] | None) -> bool:
    if not bounds1 or not bounds2:
        return False
    l1, b1, r1, t1 = bounds1
    l2, b2, r2, t2 = bounds2
    return max(l1, l2) < min(r1, r2) and max(b1, b2) < min(t1, t2)

def detect_sensor_configuration(metadata: ImageMetadata) -> tuple[str, float, str]:
    if metadata.sensor:
        sensor_lower = metadata.sensor.lower()
        if any(s in sensor_lower for s in ["sentinel-1", "ers", "palsar", "radarsat", "sar"]):
            return "sar", 0.95, "metadata"
        if any(s in sensor_lower for s in ["sentinel-2", "landsat", "modis", "worldview"]):
            return "optical", 0.95, "metadata"

    if metadata.image_type and metadata.image_type != "unknown":
        # e.g., derived from bands
        return metadata.image_type, 0.7, "band_heuristics"

    return "unknown", 0.0, "insufficient_metadata"

def validate_pair(meta1: ImageMetadata, meta2: ImageMetadata, expected_type: str) -> PairValidationResult:
    errors = []
    warnings = []

    # Check CRS
    if meta1.crs != meta2.crs:
        if meta1.crs and meta2.crs:
            errors.append(f"CRS mismatch: {meta1.crs} vs {meta2.crs}")
        else:
            warnings.append("One or both images missing CRS information")

    # Check dimensions roughly
    if meta1.width != meta2.width or meta1.height != meta2.height:
        warnings.append(f"Dimension mismatch: {meta1.width}x{meta1.height} vs {meta2.width}x{meta2.height}")
    
    # Check resolution
    if meta1.resolution and meta2.resolution:
        if abs(meta1.resolution[0] - meta2.resolution[0]) > 1e-4 or abs(meta1.resolution[1] - meta2.resolution[1]) > 1e-4:
            warnings.append(f"Resolution mismatch: {meta1.resolution} vs {meta2.resolution}")

    # Check spatial overlap
    if meta1.bounds and meta2.bounds:
        if not check_overlap(meta1.bounds, meta2.bounds):
            errors.append("Images do not overlap spatially")
    else:
        warnings.append("Missing bounds information for overlap check")

    if expected_type == "optical_sar":
        t1, _, _ = detect_sensor_configuration(meta1)
        t2, _, _ = detect_sensor_configuration(meta2)
        types = {t1, t2}
        if "optical" not in types or "sar" not in types:
            if t1 != "unknown" and t2 != "unknown":
                errors.append(f"Expected Optical+SAR pair, but found {t1} and {t2}")
            else:
                warnings.append("Could not confidently verify Optical+SAR pair from metadata")

    return PairValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
