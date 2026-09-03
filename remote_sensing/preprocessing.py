"""
SatQuery AI — Co-Registration Preprocessing (Person D - Part 1)

Checks co-registration compatibility between two ImageMetadata objects:
  1. Neither CRS can be "none"
  2. CRS strings must match
  3. Spatial resolution must match within 10% tolerance
"""

from typing import Tuple
from schemas.contracts import ImageMetadata


def check_coregistration(meta1: ImageMetadata, meta2: ImageMetadata) -> Tuple[bool, str]:
    """
    Check spatial co-registration compatibility.
    Returns (is_compatible, reason).
    """
    c1 = (meta1.crs or "").upper().strip()
    c2 = (meta2.crs or "").upper().strip()

    # Rule a: Both must have valid CRS (not "none")
    if c1 == "NONE" or c2 == "NONE" or not c1 or not c2:
        return False, "One or both images lack geospatial reference data (CRS is 'none')"

    # Rule b: CRS match
    if c1 != c2:
        return False, f"CRS mismatch: {c1} vs {c2}"

    # Rule c: Resolution within 10% tolerance
    r1, r2 = meta1.resolution_m, meta2.resolution_m
    if r1 > 0 and r2 > 0:
        diff = abs(r1 - r2) / max(r1, r2)
        if diff > 0.10:
            return False, f"Spatial resolution mismatch exceeds 10%: {r1}m vs {r2}m ({diff*100:.1f}% diff)"

    # Rule d: Passed
    return True, "Co-registration checks passed"
