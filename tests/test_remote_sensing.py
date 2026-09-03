"""
tests/test_remote_sensing.py — Tests for remote_sensing package.

Key invariant: benchmark images (PNG/JPEG) have crs="none" (string sentinel).
               check_coregistration() treats "none" as a missing CRS.
"""

import pytest
import sys
import os
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from remote_sensing.geotiff import load_benchmark_image, ImageLoadError
from remote_sensing.preprocessing import check_coregistration
from remote_sensing.metadata import validate_metadata_complete, summarize_metadata
from schemas.contracts import ImageMetadata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_meta(
    sensor="optical",
    crs="EPSG:4326",
    width=100,
    height=100,
    bands=3,
    resolution_m=10.0,
    acquisition_date=None,
    file_path="path.tif",
) -> ImageMetadata:
    """Build ImageMetadata using keyword args (Pydantic v2 requires this)."""
    return ImageMetadata(
        sensor=sensor, crs=crs, width=width, height=height,
        bands=bands, resolution_m=resolution_m,
        acquisition_date=acquisition_date, file_path=file_path,
    )


# ---------------------------------------------------------------------------
# load_benchmark_image tests
# ---------------------------------------------------------------------------

def test_load_benchmark_image_rgb(tmp_path):
    """RGB PNG → shape (3, H, W), crs='none', resolution_m=0.0."""
    path = tmp_path / "test_rgb.png"
    Image.new("RGB", (100, 100), color="red").save(path)

    data, meta = load_benchmark_image(str(path), "optical")

    assert data.shape == (3, 100, 100)
    assert meta.sensor == "optical"
    assert meta.bands == 3
    assert meta.width == 100
    assert meta.height == 100
    # Key spec check: crs is the STRING "none", not Python None
    assert meta.crs == "none", f"Expected crs='none', got crs={meta.crs!r}"
    assert meta.resolution_m == 0.0


def test_load_benchmark_image_grayscale(tmp_path):
    """Grayscale PNG → shape (1, H, W), sensor preserved."""
    path = tmp_path / "test_gray.png"
    Image.new("L", (100, 100), color=128).save(path)

    data, meta = load_benchmark_image(str(path), "sar")

    assert data.shape == (1, 100, 100)
    assert meta.sensor == "sar"
    assert meta.bands == 1
    assert meta.crs == "none"


def test_load_benchmark_image_bad_path_raises():
    """Non-existent path → ImageLoadError with helpful message."""
    with pytest.raises(ImageLoadError, match=r"not found|Failed"):
        load_benchmark_image("non_existent_file.png", "optical")


def test_load_benchmark_image_width_height_correct(tmp_path):
    """Width and height are set from the actual image dimensions."""
    path = tmp_path / "test_size.png"
    Image.new("RGB", (200, 150), color="blue").save(path)

    data, meta = load_benchmark_image(str(path), "optical")
    assert meta.width == 200
    assert meta.height == 150


# ---------------------------------------------------------------------------
# check_coregistration tests (string sentinel "none" critical)
# ---------------------------------------------------------------------------

def test_check_coregistration_passes_matching_crs():
    """Same real CRS and same resolution → passes."""
    meta1 = _make_meta("optical", "EPSG:4326", file_path="path1.tif")
    meta2 = _make_meta("sar", "EPSG:4326", file_path="path2.tif")

    ok, reason = check_coregistration(meta1, meta2)

    assert ok is True
    assert "co-registration checks passed" in reason


def test_check_coregistration_fails_crs_none_sentinel():
    """crs='none' (string sentinel) → fails with 'lack geospatial reference data'."""
    meta1 = _make_meta("optical", crs="none", file_path="bench1.png")
    meta2 = _make_meta("sar", "EPSG:4326", file_path="path2.tif")

    ok, reason = check_coregistration(meta1, meta2)

    assert ok is False
    assert "lack geospatial" in reason


def test_check_coregistration_fails_both_none_sentinel():
    """Both crs='none' → fails."""
    meta1 = _make_meta("optical", crs="none", file_path="bench1.png")
    meta2 = _make_meta("sar", crs="none", file_path="bench2.png")

    ok, reason = check_coregistration(meta1, meta2)

    assert ok is False
    assert "lack geospatial" in reason


def test_check_coregistration_fails_python_none():
    """Python None crs → treated same as 'none' sentinel → fails."""
    meta1 = _make_meta("optical", crs=None, file_path="path1.tif")
    meta2 = _make_meta("sar", "EPSG:4326", file_path="path2.tif")

    ok, reason = check_coregistration(meta1, meta2)

    assert ok is False
    assert "lack geospatial" in reason


def test_check_coregistration_fails_crs_mismatch():
    """Different CRS strings → fails with 'CRS mismatch'."""
    meta1 = _make_meta("optical", "EPSG:4326", file_path="path1.tif")
    meta2 = _make_meta("sar", "EPSG:3857", file_path="path2.tif")

    ok, reason = check_coregistration(meta1, meta2)

    assert ok is False
    assert "CRS mismatch" in reason
    assert "EPSG:4326" in reason
    assert "EPSG:3857" in reason


def test_check_coregistration_fails_resolution_mismatch():
    """10m vs 15m resolution (33% diff, > 10% threshold) → fails."""
    meta1 = _make_meta("optical", "EPSG:4326", resolution_m=10.0, file_path="p1.tif")
    meta2 = _make_meta("sar", "EPSG:4326", resolution_m=15.0, file_path="p2.tif")

    ok, reason = check_coregistration(meta1, meta2)

    assert ok is False
    assert "Resolution mismatch" in reason or "resolution" in reason.lower()


def test_check_coregistration_passes_resolution_within_tolerance():
    """10m vs 10.5m (5% diff, within 10% threshold) → passes."""
    meta1 = _make_meta("optical", "EPSG:4326", resolution_m=10.0, file_path="p1.tif")
    meta2 = _make_meta("sar", "EPSG:4326", resolution_m=10.5, file_path="p2.tif")

    ok, reason = check_coregistration(meta1, meta2)

    assert ok is True


def test_check_coregistration_skips_resolution_if_zero():
    """Zero resolution (benchmark) is skipped in resolution check."""
    meta1 = _make_meta("optical", "EPSG:4326", resolution_m=10.0, file_path="p1.tif")
    meta2 = _make_meta("sar", "EPSG:4326", resolution_m=0.0, file_path="p2.tif")

    # resolution_m=0.0 for one image means no resolution known — skip check
    ok, reason = check_coregistration(meta1, meta2)

    assert ok is True  # Should pass since 0.0 means "unknown, skip"


# ---------------------------------------------------------------------------
# validate_metadata_complete tests
# ---------------------------------------------------------------------------

def test_validate_metadata_complete_passes():
    """Valid ImageMetadata → (True, '')."""
    meta = _make_meta()
    valid, reason = validate_metadata_complete(meta)
    assert valid is True
    assert reason == ""


def test_validate_metadata_complete_fails_zero_width():
    """width=0 → fails with 'width must be > 0'."""
    meta = _make_meta(width=0)
    valid, reason = validate_metadata_complete(meta)
    assert valid is False
    assert "width" in reason.lower()


def test_validate_metadata_complete_fails_zero_height():
    """height=0 → fails."""
    meta = _make_meta(height=0)
    valid, reason = validate_metadata_complete(meta)
    assert valid is False
    assert "height" in reason.lower()


def test_validate_metadata_complete_fails_empty_sensor():
    """Empty sensor field → fails."""
    meta = _make_meta(sensor="")
    valid, reason = validate_metadata_complete(meta)
    assert valid is False
    assert "sensor" in reason.lower()


# ---------------------------------------------------------------------------
# summarize_metadata tests
# ---------------------------------------------------------------------------

def test_summarize_metadata_full():
    """Full metadata → one-line string with all key info."""
    meta = _make_meta()
    summary = summarize_metadata(meta)

    assert isinstance(summary, str)
    assert len(summary) > 10
    # Must contain sensor, dimensions, CRS
    assert any(x in summary for x in ["optical", "Optical", "OPTICAL"])
    assert "100" in summary  # width/height
    assert "EPSG:4326" in summary


def test_summarize_metadata_benchmark():
    """Benchmark image (crs='none') → summary includes 'benchmark' label."""
    meta = _make_meta(crs="none", resolution_m=0.0)
    summary = summarize_metadata(meta)

    assert "benchmark" in summary.lower() or "none" in summary.lower()
