"""
SatQuery AI — Unit Tests for Change Detection (Person C)
"""

import torch
import pytest
from PIL import Image

from schemas.contracts import ImageMetadata, SpecialistRequest
from models.change.encoder import SiameseEncoder
from models.change.difference import compute_change_magnitude
from models.change.change_head import run_change_detection


class TestChangeDetection:
    def test_siamese_weight_sharing(self):
        encoder = SiameseEncoder()
        encoder.eval()

        t1 = torch.randn(1, 3, 224, 224)

        # Same input twice -> outputs must be identical
        f1, f2 = encoder(t1, t1)
        assert torch.allclose(f1, f2, atol=1e-5)

    def test_compute_change_magnitude_same_vs_different(self):
        f1 = torch.ones(1, 512, 7, 7)
        f2 = torch.ones(1, 512, 7, 7)
        # Identical -> magnitude near 0
        mag_same = compute_change_magnitude(f1, f2)
        assert mag_same < 0.05

        f_diff = torch.zeros(1, 512, 7, 7)
        mag_diff = compute_change_magnitude(f1, f_diff)
        assert mag_diff > mag_same

    def test_run_change_detection_rejects_single_image(self):
        req = SpecialistRequest(
            query="What changed?",
            images=[ImageMetadata(file_path="/tmp/fake.png")]
        )
        resp = run_change_detection(req)
        assert resp.status == "error"
        assert "requires exactly 2 images" in resp.error_message

    def test_run_change_detection_smoke_test(self, tmp_path):
        # Create 2 temporary PNG files
        p1 = str(tmp_path / "img1.png")
        p2 = str(tmp_path / "img2.png")

        Image.new("RGB", (100, 100), color="white").save(p1)
        Image.new("RGB", (100, 100), color="black").save(p2)

        req = SpecialistRequest(
            query="Has the land cover changed?",
            images=[
                ImageMetadata(sensor="optical", crs="EPSG:4326", file_path=p1),
                ImageMetadata(sensor="optical", crs="EPSG:4326", file_path=p2),
            ]
        )

        resp = run_change_detection(req)
        assert resp.status == "success"
        assert resp.task == "change_vqa"
        assert resp.confidence > 0.0
