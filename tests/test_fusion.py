"""
tests/test_fusion.py — Tests for models.fusion package.

Tests requiring torch are skipped if torch is not installed.
Validation tests (wrong image counts, wrong sensors) run without torch.
"""
import pytest
import sys
import os
import unittest.mock
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas.contracts import SpecialistRequest, ImageMetadata

# Fusion validation tests (don't require torch for the rejections)
# but fusion_head.py imports torch at module level via encoders.
# We use importorskip for that module.
torch = pytest.importorskip("torch", reason="torch not installed; skipping model-dependent tests")

from models.fusion.encoders import optical_encoder, sar_encoder
from models.fusion.fusion_head import run_optical_sar_fusion


def _opt(path="path1.tif", crs="EPSG:4326") -> ImageMetadata:
    return ImageMetadata(sensor="optical", crs=crs, width=100, height=100,
                         bands=3, resolution_m=10.0, file_path=path)


def _sar(path="path2.tif", crs="EPSG:4326") -> ImageMetadata:
    return ImageMetadata(sensor="sar", crs=crs, width=100, height=100,
                         bands=2, resolution_m=10.0, file_path=path)


def test_run_optical_sar_fusion_rejects_two_optical():
    req = SpecialistRequest(query="test", images=[_opt(), _opt("path2.tif")], task_hint="")
    resp = run_optical_sar_fusion(req)
    assert resp.status == "error"
    # Message should reference sensor requirement
    assert "optical" in resp.error_message.lower() or "sar" in resp.error_message.lower()


def test_run_optical_sar_fusion_rejects_two_sar():
    req = SpecialistRequest(query="test", images=[_sar(), _sar("path2.tif")], task_hint="")
    resp = run_optical_sar_fusion(req)
    assert resp.status == "error"


def test_run_optical_sar_fusion_rejects_one_image():
    req = SpecialistRequest(query="test", images=[_opt()], task_hint="")
    resp = run_optical_sar_fusion(req)
    assert resp.status == "error"
    assert "2" in resp.error_message  # Message should mention 2 images


def test_run_optical_sar_fusion_rejects_misaligned_pair():
    """Optical (EPSG:4326) + SAR (EPSG:3857) → CRS mismatch → error."""
    req = SpecialistRequest(
        query="test",
        images=[_opt(crs="EPSG:4326"), _sar(crs="EPSG:3857")],
        task_hint="",
    )
    resp = run_optical_sar_fusion(req)
    assert resp.status == "error"
    assert "CRS" in resp.error_message or "crs" in resp.error_message.lower()


def test_optical_sar_encoders_have_independent_weights():
    """optical_encoder and sar_encoder must be separate objects with independent parameters."""
    assert optical_encoder is not sar_encoder, "Should be separate instances"

    opt_params = list(optical_encoder.parameters())
    sar_params = list(sar_encoder.parameters())
    assert len(opt_params) > 0, "optical_encoder has no parameters"
    assert len(sar_params) > 0, "sar_encoder has no parameters"

    # Parameters should be independent objects (not shared)
    assert opt_params[0] is not sar_params[0], "First parameters should be independent"


@unittest.mock.patch("models.fusion.fusion_head.check_coregistration")
def test_run_optical_sar_fusion_e2e(mock_check_coregistration, tmp_path):
    """End-to-end smoke test: mock coregistration, run fusion, verify response."""
    mock_check_coregistration.return_value = (True, "ok")

    opt_path = tmp_path / "opt.png"
    sar_path = tmp_path / "sar.png"
    Image.new("RGB", (64, 64), color="blue").save(opt_path)
    Image.new("L", (64, 64), color=128).save(sar_path)

    req = SpecialistRequest(
        query="Analyze flooded areas",
        images=[
            ImageMetadata(sensor="optical", crs=None, width=64, height=64,
                          bands=3, resolution_m=0.0, file_path=str(opt_path)),
            ImageMetadata(sensor="sar", crs=None, width=64, height=64,
                          bands=1, resolution_m=0.0, file_path=str(sar_path)),
        ],
        task_hint="",
    )

    resp = run_optical_sar_fusion(req)

    assert resp.status == "success"
    assert resp.task == "optical_sar_fusion"
    assert len(resp.answer) > 10
    assert "Fusion signal" in resp.answer or "optical" in resp.answer.lower()
