"""
remote_sensing/preprocessing.py — Spatial co-registration validation

SENTINEL CONVENTION
-------------------
crs="none" is the project-wide string sentinel meaning "this image has no
geospatial coordinate reference system". It is set by load_benchmark_image()
for PNG/JPEG benchmark data. check_coregistration() treats "none" as a
hard failure — there is no sensible way to assert two images are co-registered
when one (or both) has no spatial reference frame.

WHY STRING "none" INSTEAD OF Python None?
------------------------------------------
Using a lowercase string sentinel makes the check deterministic across
different code paths (e.g., values loaded from SQLite TEXT columns, JSON
serialization, or string comparisons) without needing special None-handling
in every comparison. It also makes log messages self-explanatory:
    crs="none"  →  immediately clear this is a no-CRS image
    crs=None    →  ambiguous: missing, not yet set, or genuinely absent?
"""

import logging
from schemas.contracts import ImageMetadata

logger = logging.getLogger(__name__)

_NO_CRS: str = "none"


def check_coregistration(
    meta1: ImageMetadata,
    meta2: ImageMetadata,
) -> tuple[bool, str]:
    """
    Validate that two images are spatially co-registered before bi-temporal
    analysis (change detection) or multi-modal fusion (optical-SAR).

    Four checks are performed in strict priority order. Each check fails fast
    with a specific, human-readable reason so the caller can surface it directly
    to the user without further diagnosis.

    Check (a): Both images must have a real CRS (not the sentinel "none").
    Check (b): CRS strings must match exactly (case-insensitive).
    Check (c): Ground resolution must agree within 10 % relative tolerance.
    Check (d): All checks passed — images are considered co-registered.

    Args:
        meta1: Metadata for the first image (e.g., the "before" or optical image).
        meta2: Metadata for the second image (e.g., the "after" or SAR image).

    Returns:
        Tuple of (is_coregistered: bool, reason: str).
        On success: (True, "co-registration checks passed").
        On failure: (False, <specific reason>).
    """
    # ------------------------------------------------------------------
    # Check (a) — both images must have a real CRS, not the "none" sentinel
    # ------------------------------------------------------------------
    crs1 = (meta1.crs or _NO_CRS).strip().lower()
    crs2 = (meta2.crs or _NO_CRS).strip().lower()

    if crs1 == _NO_CRS or crs2 == _NO_CRS:
        missing = []
        if crs1 == _NO_CRS:
            missing.append(f"image 1 ('{meta1.file_path}')")
        if crs2 == _NO_CRS:
            missing.append(f"image 2 ('{meta2.file_path}')")
        reason = (
            f"one or both images lack geospatial reference data "
            f"({', '.join(missing)}). "
            "Benchmark images (PNG/JPEG with crs='none') cannot be co-registered. "
            "Use GeoTIFF files with a valid CRS for change detection or fusion."
        )
        logger.warning("check_coregistration FAILED (no CRS): %s", reason)
        return False, reason

    # ------------------------------------------------------------------
    # Check (b) — CRS strings must match (case-insensitive)
    # ------------------------------------------------------------------
    # Strip whitespace and compare uppercase to handle minor formatting
    # differences (e.g., "EPSG:4326" vs "epsg:4326").
    if crs1 != crs2:
        reason = (
            f"CRS mismatch: '{meta1.crs}' vs '{meta2.crs}'. "
            "Both images must share the same Coordinate Reference System. "
            "Reproject one image to match the other before analysis."
        )
        logger.warning("check_coregistration FAILED (CRS mismatch): %s", reason)
        return False, reason

    # ------------------------------------------------------------------
    # Check (c) — resolution within 10 % relative tolerance
    # ------------------------------------------------------------------
    r1 = meta1.resolution_m
    r2 = meta2.resolution_m

    if r1 > 0.0 and r2 > 0.0:
        rel_diff = abs(r1 - r2) / max(r1, r2)
        if rel_diff > 0.10:
            reason = (
                f"Resolution mismatch: {r1:.1f}m vs {r2:.1f}m "
                f"({rel_diff * 100:.0f}% relative difference, threshold is 10%). "
                "Resample one image to match the other's resolution before analysis."
            )
            logger.warning("check_coregistration FAILED (resolution): %s", reason)
            return False, reason

    # ------------------------------------------------------------------
    # Check (d) — all checks passed
    # ------------------------------------------------------------------
    logger.info(
        "check_coregistration PASSED: CRS=%s, res=%.1fm/%.1fm",
        meta1.crs, r1, r2,
    )
    return True, "co-registration checks passed"
