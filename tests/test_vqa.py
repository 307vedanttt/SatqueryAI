"""
SatQuery AI — Mocked Unit Tests for VQA Module (Person B)

Runs in CI with mocked model_loader.
"""

import pytest
from unittest.mock import MagicMock, patch

from schemas.contracts import ImageMetadata, SpecialistRequest


class TestVQAModuleMocked:
    @pytest.fixture
    def req_1_img(self):
        return SpecialistRequest(
            query="Describe this image",
            images=[ImageMetadata(file_path="/tmp/fake.png")]
        )

    @pytest.fixture
    def req_2_img(self):
        return SpecialistRequest(
            query="Describe this image",
            images=[ImageMetadata(file_path="/tmp/fake1.png"), ImageMetadata(file_path="/tmp/fake2.png")]
        )

    def test_vqa_rejects_multi_image(self, req_2_img):
        from models.vqa.vqa import run_vqa
        resp = run_vqa(req_2_img)
        assert resp.status == "error"
        assert "requires exactly 1 image" in resp.error_message

    def test_captioning_rejects_multi_image(self, req_2_img):
        from models.vqa.captioning import run_captioning
        resp = run_captioning(req_2_img)
        assert resp.status == "error"

    def test_grounding_rejects_multi_image(self, req_2_img):
        from models.vqa.grounding import run_grounding
        resp = run_grounding(req_2_img)
        assert resp.status == "error"

    def test_bbox_parser(self):
        from models.vqa.grounding import parse_bbox_from_text
        text = "The building is located at [100, 200, 500, 600]."
        bbox = parse_bbox_from_text(text, label="building")
        assert bbox is not None
        assert bbox.xmin == 100
        assert bbox.ymin == 200
        assert bbox.xmax == 500
        assert bbox.ymax == 600

    def test_bbox_parser_returns_none_on_invalid_text(self):
        from models.vqa.grounding import parse_bbox_from_text
        text = "No coordinates here."
        bbox = parse_bbox_from_text(text)
        assert bbox is None
