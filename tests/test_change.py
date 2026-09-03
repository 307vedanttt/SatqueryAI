"""
tests/test_change.py — Tests for models.change package.

Tests requiring torch are skipped if torch is not installed.
The validation tests (rejects wrong image counts) run without torch.
"""
import pytest
import sys
import os
from PIL import Image

# Ensure repo root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas.contracts import SpecialistRequest, ImageMetadata

# Try to import torch — skip torch-dependent tests if not available
torch = pytest.importorskip("torch", reason="torch not installed; skipping model-dependent tests")

from models.change.encoder import SiameseEncoder
from models.change.difference import compute_change_magnitude
from models.change.change_head import run_change_detection


def _make_img_meta(path="img.jpg", sensor="optical") -> ImageMetadata:
    return ImageMetadata(
        sensor=sensor,
        crs="EPSG:4326",
        width=64,
        height=64,
        bands=3,
        resolution_m=10.0,
        acquisition_date="2024-01-01",
        file_path=path,
    )


# ---------------------------------------------------------------------------
# Validation tests (no torch required — run even without GPU)
# ---------------------------------------------------------------------------

def test_run_change_detection_rejects_zero_images():
    req = SpecialistRequest(query="test", images=[], task_hint="change_detection")
    res = run_change_detection(req)
    assert res.status == "error"


def test_run_change_detection_rejects_one_image():
    req = SpecialistRequest(query="test", images=[_make_img_meta()], task_hint="change_detection")
    res = run_change_detection(req)
    assert res.status == "error"


def test_run_change_detection_rejects_three_images():
    meta = _make_img_meta()
    req = SpecialistRequest(query="test", images=[meta, meta, meta], task_hint="change_detection")
    res = run_change_detection(req)
    assert res.status == "error"


# ---------------------------------------------------------------------------
# Torch-dependent tests — skipped if torch not installed
# ---------------------------------------------------------------------------

def test_siamese_encoder_same_output_for_identical_images():
    """Identical input → identical feature vectors (shared-weight invariant)."""
    t1 = torch.rand(1, 3, 224, 224)
    encoder = SiameseEncoder()
    f1, f2 = encoder(t1, t1)
    assert torch.allclose(f1, f2), "Identical inputs must produce identical features"


def test_siamese_encoder_different_output_for_different_images():
    """Different inputs → different feature vectors."""
    t1 = torch.rand(1, 3, 224, 224)
    t2 = torch.rand(1, 3, 224, 224)
    encoder = SiameseEncoder()
    f1, f2 = encoder(t1, t2)
    assert not torch.allclose(f1, f2), "Different inputs should produce different features"


def test_siamese_encoder_uses_shared_weights():
    """SiameseEncoder.backbone must be a single nn.Module instance (shared weights)."""
    encoder = SiameseEncoder()
    assert isinstance(encoder.backbone, torch.nn.Module)
    # Verify it's a single backbone (not two separate ones)
    assert hasattr(encoder, "backbone")
    assert not hasattr(encoder, "backbone2")


def test_compute_change_magnitude_high_for_different():
    """Very different tensors (one positive, one negative) → high magnitude."""
    t1 = torch.ones(512) * 0.8
    t2 = -t1
    mag = compute_change_magnitude(t1, t2)
    assert mag > 0.3, f"Expected magnitude > 0.3 for opposing tensors, got {mag}"


def test_compute_change_magnitude_low_for_identical():
    """Identical tensors → near-zero change magnitude."""
    t1 = torch.rand(512)
    mag = compute_change_magnitude(t1, t1)
    assert mag < 0.01, f"Expected magnitude < 0.01 for identical tensors, got {mag}"


def test_compute_change_magnitude_returns_float_in_range():
    """Change magnitude must be a float in [0, 1]."""
    t1 = torch.rand(512)
    t2 = torch.rand(512)
    mag = compute_change_magnitude(t1, t2)
    assert isinstance(mag, float), f"Expected float, got {type(mag)}"
    assert 0.0 <= mag <= 1.0, f"Magnitude {mag} outside [0, 1]"


def test_run_change_detection_e2e(tmp_path):
    """End-to-end smoke test: two synthetic images → success response."""
    img1_path = str(tmp_path / "img1.png")
    img2_path = str(tmp_path / "img2.png")

    Image.new("RGB", (64, 64), color="red").save(img1_path)
    Image.new("RGB", (64, 64), color="blue").save(img2_path)

    req = SpecialistRequest(
        query="What changed?",
        images=[
            _make_img_meta(img1_path),
            _make_img_meta(img2_path),
        ],
        task_hint="change_vqa",
    )
    res = run_change_detection(req)

    assert res.status == "success"
    assert res.task in ("change_detection", "change_vqa")
    assert len(res.answer) > 10, "Answer should be a non-trivial string"
    assert "Siamese" in res.model_used
