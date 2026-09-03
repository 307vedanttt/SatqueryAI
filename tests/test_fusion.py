"""
SatQuery AI — Unit Tests for Optical-SAR Fusion (Person D - Part 2)
"""

import pytest
import torch
from PIL import Image

from schemas.contracts import ImageMetadata, SpecialistRequest
from models.fusion.encoders import OpticalEncoder, SAREncoder
from models.fusion.fusion import CrossAttentionFusion
from models.fusion.fusion_head import run_optical_sar_fusion


class TestOpticalSARFusion:
    def test_independent_encoder_weights(self):
        opt = OpticalEncoder()
        sar = SAREncoder()

        # Encoders must NOT share weights
        assert opt.backbone is not sar.backbone

        x = torch.randn(1, 3, 224, 224)
        f_opt = opt(x)
        f_sar = sar(x)
        assert f_opt.shape == f_sar.shape

    def test_cross_attention_fusion_forward(self):
        fusion = CrossAttentionFusion(embed_dim=512, num_heads=4)
        f_opt = torch.randn(1, 512, 7, 7)
        f_sar = torch.randn(1, 512, 7, 7)

        fused = fusion(f_opt, f_sar)
        assert fused.shape == (1, 512, 7, 7)

    def test_run_optical_sar_fusion_rejects_non_optical_sar_pair(self):
        req = SpecialistRequest(
            query="Fuse",
            images=[
                ImageMetadata(sensor="optical", crs="EPSG:4326", file_path="/a.tif"),
                ImageMetadata(sensor="optical", crs="EPSG:4326", file_path="/b.tif"),
            ]
        )
        resp = run_optical_sar_fusion(req)
        assert resp.status == "error"
        assert "requires 1 optical and 1 SAR" in resp.error_message

    def test_run_optical_sar_fusion_smoke_test(self, tmp_path):
        p1 = str(tmp_path / "opt.png")
        p2 = str(tmp_path / "sar.png")

        Image.new("RGB", (100, 100), color="green").save(p1)
        Image.new("RGB", (100, 100), color="gray").save(p2)

        req = SpecialistRequest(
            query="Fuse optical and SAR",
            images=[
                ImageMetadata(sensor="optical", crs="EPSG:4326", file_path=p1),
                ImageMetadata(sensor="sar", crs="EPSG:4326", file_path=p2),
            ]
        )

        resp = run_optical_sar_fusion(req)
        assert resp.status == "success"
        assert resp.task == "optical_sar_fusion"
        assert resp.confidence > 0.8
