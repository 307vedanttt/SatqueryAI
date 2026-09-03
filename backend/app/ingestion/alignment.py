"""
SatQuery AI — Ingestion: Pair Alignment Validator

Validates that two uploaded images form a valid geospatial pair
before any analysis is attempted.

Rules (in order):
  1. Both files must be valid GeoTIFFs with CRS
  2. CRS must match
  3. Resolution must match (within tolerance)
  4. Bounds must spatially overlap
  5. Dimensions should be compatible

Never allow AI to compensate for misaligned inputs.
"""

from dataclasses import dataclass
from typing import Optional

from app.core.logging import get_logger
from app.models.schemas import ImageMetadata

logger = get_logger(__name__)

# Tolerance for floating-point resolution comparison (10% relative difference)
RESOLUTION_TOLERANCE = 0.10


@dataclass
class PairValidationResult:
    valid: bool
    error_code: str | None = None
    message: str | None = None
    details: dict | None = None
    overlap_fraction: float | None = None


def validate_pair(img1: ImageMetadata, img2: ImageMetadata) -> PairValidationResult:
    """
    Validate that two images form a valid geospatial pair.
    Returns a PairValidationResult with detailed diagnostics.
    """
    # 1. Both must be GeoTIFF
    if not img1.is_geotiff or not img2.is_geotiff:
        return PairValidationResult(
            valid=False,
            error_code="PAIR_NOT_GEOTIFF",
            message="Both images must be GeoTIFF files for pair analysis.",
        )

    # 2. Both must have CRS
    if not img1.crs or not img2.crs:
        return PairValidationResult(
            valid=False,
            error_code="INVALID_CRS",
            message="One or both images are missing a coordinate reference system.",
        )

    # 3. CRS must match
    if _normalize_crs(img1.crs) != _normalize_crs(img2.crs):
        return PairValidationResult(
            valid=False,
            error_code="PAIR_ALIGNMENT_ERROR",
            message=(
                f"CRS mismatch: image 1 has {img1.crs}, image 2 has {img2.crs}. "
                "Reproject one image before analysis."
            ),
            details={"crs_1": img1.crs, "crs_2": img2.crs},
        )

    # 4. Resolution must match within tolerance
    if img1.resolution and img2.resolution:
        res_ok, res_detail = _check_resolution(img1.resolution, img2.resolution)
        if not res_ok:
            return PairValidationResult(
                valid=False,
                error_code="PAIR_ALIGNMENT_ERROR",
                message="Image resolutions differ significantly. Resample before analysis.",
                details=res_detail,
            )

    # 5. Bounds must overlap
    if img1.bounds and img2.bounds:
        overlap = _compute_overlap_fraction(img1.bounds, img2.bounds)
        if overlap <= 0.0:
            return PairValidationResult(
                valid=False,
                error_code="PAIR_ALIGNMENT_ERROR",
                message="The uploaded images have no spatial overlap and cannot be compared.",
                details={"overlap_fraction": 0.0},
            )
        return PairValidationResult(
            valid=True,
            message="Images are spatially aligned and form a valid pair.",
            overlap_fraction=overlap,
        )

    # Passed all checks with available metadata
    return PairValidationResult(valid=True, message="Pair validation passed.")


def _normalize_crs(crs_str: str) -> str:
    """Normalize CRS string for comparison (uppercase, strip spaces)."""
    return crs_str.upper().strip().replace(" ", "")


def _check_resolution(
    res1: tuple[float, float],
    res2: tuple[float, float],
) -> tuple[bool, dict]:
    """Check if resolutions are within tolerance."""
    x_diff = abs(res1[0] - res2[0]) / max(res1[0], res2[0], 1e-9)
    y_diff = abs(res1[1] - res2[1]) / max(res1[1], res2[1], 1e-9)
    ok = x_diff <= RESOLUTION_TOLERANCE and y_diff <= RESOLUTION_TOLERANCE
    return ok, {
        "resolution_1": res1,
        "resolution_2": res2,
        "x_diff_fraction": x_diff,
        "y_diff_fraction": y_diff,
    }


def _compute_overlap_fraction(
    bounds1: tuple[float, float, float, float],
    bounds2: tuple[float, float, float, float],
) -> float:
    """
    Compute the fraction of image1's area that overlaps with image2.
    bounds = (left, bottom, right, top) in CRS units.
    Returns 0.0 if there is no overlap.
    """
    left = max(bounds1[0], bounds2[0])
    bottom = max(bounds1[1], bounds2[1])
    right = min(bounds1[2], bounds2[2])
    top = min(bounds1[3], bounds2[3])

    if right <= left or top <= bottom:
        return 0.0

    overlap_area = (right - left) * (top - bottom)
    img1_area = (bounds1[2] - bounds1[0]) * (bounds1[3] - bounds1[1])

    if img1_area <= 0:
        return 0.0

    return min(1.0, overlap_area / img1_area)
