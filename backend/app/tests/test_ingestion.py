"""
SatQuery AI — Backend Tests: Ingestion

Tests for file validation, GeoTIFF metadata extraction, and pair alignment.
"""

import io
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import (
    CorruptedRasterError,
    FileTooLargeError,
    InvalidFileFormatError,
)
from app.core.security import (
    generate_internal_filename,
    sanitize_filename,
    validate_extension,
    validate_file_size,
)
from app.ingestion.alignment import validate_pair
from app.models.schemas import ImageMetadata


# ---- Security / Validation Tests ----------------------------------------

class TestFileValidation:
    def test_valid_tiff_extension(self):
        ext = validate_extension("image.tif")
        assert ext == ".tif"

    def test_valid_tiff_upper(self):
        ext = validate_extension("IMAGE.TIFF")
        assert ext == ".tiff"

    def test_valid_png(self):
        ext = validate_extension("photo.png")
        assert ext == ".png"

    def test_invalid_extension_raises(self):
        with pytest.raises(InvalidFileFormatError) as exc_info:
            validate_extension("malware.exe")
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"

    def test_invalid_pdf_raises(self):
        with pytest.raises(InvalidFileFormatError):
            validate_extension("document.pdf")

    def test_file_size_ok(self):
        validate_file_size(1024 * 1024)  # 1 MB — should not raise

    def test_file_too_large_raises(self):
        with pytest.raises(FileTooLargeError) as exc_info:
            validate_file_size(200 * 1024 * 1024)  # 200 MB
        assert exc_info.value.error_code == "FILE_TOO_LARGE"

    def test_sanitize_filename_removes_special_chars(self):
        result = sanitize_filename("../../etc/passwd.tif")
        # Should not contain path separators or dots outside extension
        assert ".." not in result
        assert "/" not in result

    def test_generate_internal_filename_is_unique(self):
        names = {generate_internal_filename(".tif") for _ in range(100)}
        assert len(names) == 100  # All unique

    def test_generate_internal_filename_has_extension(self):
        name = generate_internal_filename(".tiff")
        assert name.endswith(".tiff")


# ---- Pair Alignment Tests ------------------------------------------------

def _make_meta(
    is_geotiff=True,
    crs="EPSG:4326",
    resolution=(10.0, 10.0),
    bounds=(0.0, 0.0, 1.0, 1.0),
    image_type="optical",
    acquisition_date=None,
) -> ImageMetadata:
    return ImageMetadata(
        filename="test.tif",
        is_geotiff=is_geotiff,
        crs=crs,
        resolution=resolution,
        bounds=bounds,
        image_type=image_type,
        acquisition_date=acquisition_date,
    )


class TestPairAlignment:
    def test_valid_aligned_pair(self):
        img1 = _make_meta()
        img2 = _make_meta()
        result = validate_pair(img1, img2)
        assert result.valid is True

    def test_one_not_geotiff(self):
        img1 = _make_meta(is_geotiff=False)
        img2 = _make_meta()
        result = validate_pair(img1, img2)
        assert result.valid is False
        assert result.error_code == "PAIR_NOT_GEOTIFF"

    def test_crs_mismatch(self):
        img1 = _make_meta(crs="EPSG:4326")
        img2 = _make_meta(crs="EPSG:32643")
        result = validate_pair(img1, img2)
        assert result.valid is False
        assert result.error_code == "PAIR_ALIGNMENT_ERROR"

    def test_resolution_mismatch_large(self):
        img1 = _make_meta(resolution=(10.0, 10.0))
        img2 = _make_meta(resolution=(100.0, 100.0))  # 10x difference
        result = validate_pair(img1, img2)
        assert result.valid is False

    def test_non_overlapping_bounds(self):
        img1 = _make_meta(bounds=(0.0, 0.0, 1.0, 1.0))
        img2 = _make_meta(bounds=(5.0, 5.0, 6.0, 6.0))  # No overlap
        result = validate_pair(img1, img2)
        assert result.valid is False

    def test_missing_crs(self):
        img1 = _make_meta(crs=None)
        img2 = _make_meta()
        result = validate_pair(img1, img2)
        assert result.valid is False
        assert result.error_code == "INVALID_CRS"

    def test_partial_overlap_valid(self):
        img1 = _make_meta(bounds=(0.0, 0.0, 2.0, 2.0))
        img2 = _make_meta(bounds=(1.0, 1.0, 3.0, 3.0))  # 25% overlap
        result = validate_pair(img1, img2)
        assert result.valid is True
        assert result.overlap_fraction > 0


# ---- Raster Metadata Tests (without GDAL) --------------------------------

class TestRasterMetadata:
    def test_image_metadata_defaults(self):
        meta = ImageMetadata(filename="test.tif")
        assert meta.crs is None
        assert meta.width is None
        assert meta.is_geotiff is False

    def test_image_metadata_full(self):
        meta = ImageMetadata(
            filename="scene.tif",
            width=2048,
            height=2048,
            bands=4,
            crs="EPSG:4326",
            resolution=(10.0, 10.0),
            bounds=(80.0, 20.0, 81.0, 21.0),
            is_geotiff=True,
            image_type="multispectral",
        )
        assert meta.width == 2048
        assert meta.crs == "EPSG:4326"
        assert meta.is_geotiff is True
        assert meta.image_type == "multispectral"

    @patch("app.ingestion.raster.RASTERIO_AVAILABLE", False)
    def test_raster_extraction_without_rasterio_raises(self):
        from app.ingestion.raster import extract_raster_metadata
        with pytest.raises(ImportError):
            extract_raster_metadata("/fake/path.tif", "fake.tif")
