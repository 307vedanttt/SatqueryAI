"""
SatQuery AI — Unit Tests for Remote Sensing Ingestion (Person D)
"""

import pytest
from PIL import Image

from schemas.contracts import ImageMetadata
from remote_sensing.geotiff import load_benchmark_image
from remote_sensing.preprocessing import check_coregistration
from remote_sensing.metadata import validate_metadata_complete, summarize_metadata


class TestRemoteSensingIngestion:
    def test_load_benchmark_image(self, tmp_path):
        p = str(tmp_path / "test.png")
        Image.new("RGB", (200, 150), color="blue").save(p)

        arr, meta = load_benchmark_image(p, sensor="optical")
        assert arr.shape == (150, 200, 3)
        assert meta.width == 200
        assert meta.height == 150
        assert meta.crs == "none"
        assert meta.resolution_m == 0.0

    def test_check_coregistration_matching(self):
        m1 = ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/a.tif")
        m2 = ImageMetadata(sensor="sar", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/b.tif")
        ok, reason = check_coregistration(m1, m2)
        assert ok is True

    def test_check_coregistration_crs_none(self):
        m1 = ImageMetadata(sensor="optical", crs="none", file_path="/a.png")
        m2 = ImageMetadata(sensor="optical", crs="EPSG:4326", file_path="/b.tif")
        ok, reason = check_coregistration(m1, m2)
        assert ok is False
        assert "lack geospatial reference data" in reason

    def test_check_coregistration_crs_mismatch(self):
        m1 = ImageMetadata(sensor="optical", crs="EPSG:4326", file_path="/a.tif")
        m2 = ImageMetadata(sensor="optical", crs="EPSG:32643", file_path="/b.tif")
        ok, reason = check_coregistration(m1, m2)
        assert ok is False
        assert "CRS mismatch" in reason

    def test_validate_metadata_complete(self):
        m_valid = ImageMetadata(sensor="optical", crs="EPSG:4326", width=10, height=10, bands=3, resolution_m=10.0, file_path="/a.tif")
        ok, _ = validate_metadata_complete(m_valid)
        assert ok is True

        m_invalid = ImageMetadata(sensor="optical", crs="EPSG:4326", width=0, height=10, bands=3, resolution_m=10.0, file_path="/a.tif")
        ok, reason = validate_metadata_complete(m_invalid)
        assert ok is False
        assert "Invalid image dimensions" in reason

    def test_summarize_metadata(self):
        m = ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, bands=3, resolution_m=10.0, file_path="/a.tif")
        summary = summarize_metadata(m)
        assert "Optical" in summary
        assert "100x100px" in summary
        assert "EPSG:4326" in summary
