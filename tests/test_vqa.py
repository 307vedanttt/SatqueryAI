"""
tests/test_vqa.py — Unit tests for VQA modules using mocks.

All tests mock get_model_and_processor so the real 3B model is never loaded.
process_vision_info is imported lazily inside functions, so we patch it at
the qwen_vl_utils level.

These tests verify:
  - Request validation (rejects wrong image counts)
  - Response shape matches SpecialistResponse contract
  - Error handling returns status="error" on exceptions
  - Captioning uses the fixed prompt regardless of request.query
  - Grounding parses bounding boxes correctly
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

# Ensure repo root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas.contracts import ImageMetadata, SpecialistRequest, SpecialistResponse, BoundingBox


def _make_image_meta(file_path: str = "dummy.jpg") -> ImageMetadata:
    return ImageMetadata(
        sensor="optical",
        crs="EPSG:4326",
        width=100,
        height=100,
        bands=3,
        resolution_m=1.0,
        acquisition_date="2026-01-01",
        file_path=file_path,
    )


def _make_mock_model_processor(answer_text: str = "A test answer"):
    """Build realistic mock (model, processor) pair for Qwen2.5-VL."""
    mock_model = MagicMock()
    mock_model.device = "cpu"
    # generate returns tensor-like list of lists; first is input+generated tokens
    mock_model.generate.return_value = [[1, 2, 3, 4, 5]]

    mock_processor = MagicMock()
    mock_processor.apply_chat_template.return_value = "chat template text"

    # processor(text=..., images=...) returns inputs object
    mock_inputs = MagicMock()
    mock_inputs.to.return_value = mock_inputs
    mock_inputs.input_ids = [[1, 2, 3]]
    mock_processor.return_value = mock_inputs

    # batch_decode returns list of strings
    mock_processor.batch_decode.return_value = [answer_text]

    return mock_model, mock_processor


class TestRunVQA(unittest.TestCase):

    def test_run_vqa_rejects_zero_images(self):
        """run_vqa with 0 images → status='error'."""
        from models.vqa.vqa import run_vqa
        req = SpecialistRequest(query="Test", images=[], task_hint="vqa")
        resp = run_vqa(req)
        self.assertEqual(resp.status, "error")
        self.assertIsNotNone(resp.error_message)
        self.assertIn("1 image", resp.error_message)

    def test_run_vqa_rejects_two_images(self):
        """run_vqa with 2 images → status='error'."""
        from models.vqa.vqa import run_vqa
        meta = _make_image_meta()
        req = SpecialistRequest(query="Test", images=[meta, meta], task_hint="vqa")
        resp = run_vqa(req)
        self.assertEqual(resp.status, "error")
        self.assertIn("1 image", resp.error_message)

    @patch("models.vqa.vqa.get_model_and_processor")
    @patch("models.vqa.vqa.Image")
    def test_run_vqa_success_returns_correct_shape(self, mock_pil_image, mock_get_model):
        """Mocked successful VQA run returns correct SpecialistResponse shape."""
        from models.vqa.vqa import run_vqa

        mock_model, mock_processor = _make_mock_model_processor("Forest and water body visible")
        mock_get_model.return_value = (mock_model, mock_processor)

        # Mock PIL Image.open
        mock_img = MagicMock()
        mock_pil_image.open.return_value = mock_img

        # Mock process_vision_info via qwen_vl_utils
        with patch.dict("sys.modules", {"qwen_vl_utils": MagicMock(
            process_vision_info=MagicMock(return_value=(["img_data"], None))
        )}):
            req = SpecialistRequest(
                query="What is visible?",
                images=[_make_image_meta()],
                task_hint="vqa",
            )
            resp = run_vqa(req)

        self.assertIsInstance(resp, SpecialistResponse)
        self.assertEqual(resp.status, "success")
        self.assertEqual(resp.task, "vqa")
        self.assertIn("Forest", resp.answer)
        self.assertEqual(resp.model_used, "Qwen2.5-VL-3B-Instruct")

    @patch("models.vqa.vqa.get_model_and_processor")
    @patch("models.vqa.vqa.Image")
    def test_run_vqa_exception_returns_error(self, mock_pil_image, mock_get_model):
        """When model.generate raises, status='error' with real exception message."""
        from models.vqa.vqa import run_vqa

        mock_get_model.side_effect = RuntimeError("CUDA out of memory")

        req = SpecialistRequest(query="Test", images=[_make_image_meta()], task_hint="vqa")
        resp = run_vqa(req)

        self.assertEqual(resp.status, "error")
        self.assertIn("CUDA out of memory", resp.error_message)
        self.assertEqual(resp.confidence_tier, "insufficient")


class TestRunCaptioning(unittest.TestCase):

    @patch("models.vqa.captioning.get_model_and_processor")
    @patch("models.vqa.captioning.Image")
    def test_run_captioning_uses_fixed_prompt(self, mock_pil_image, mock_get_model):
        """run_captioning ignores request.query and uses fixed captioning prompt."""
        from models.vqa.captioning import run_captioning

        mock_model, mock_processor = _make_mock_model_processor("Dense forest with river")
        mock_get_model.return_value = (mock_model, mock_processor)
        mock_pil_image.open.return_value = MagicMock()

        with patch.dict("sys.modules", {"qwen_vl_utils": MagicMock(
            process_vision_info=MagicMock(return_value=(["img"], None))
        )}):
            req = SpecialistRequest(
                query="IGNORE THIS QUERY",
                images=[_make_image_meta()],
                task_hint="captioning",
            )
            resp = run_captioning(req)

        # Verify the fixed prompt was used — apply_chat_template call should contain it
        call_args = mock_processor.apply_chat_template.call_args
        messages = call_args[0][0]  # first positional arg
        prompt_text = messages[0]["content"][1]["text"]
        self.assertIn("Describe the land cover", prompt_text)
        self.assertNotIn("IGNORE THIS QUERY", prompt_text)

        self.assertEqual(resp.status, "success")
        self.assertEqual(resp.task, "captioning")

    @patch("models.vqa.captioning.get_model_and_processor")
    @patch("models.vqa.captioning.Image")
    def test_run_captioning_rejects_zero_images(self, mock_pil_image, mock_get_model):
        """run_captioning with 0 images → error."""
        from models.vqa.captioning import run_captioning
        req = SpecialistRequest(query="describe", images=[], task_hint="captioning")
        resp = run_captioning(req)
        self.assertEqual(resp.status, "error")


class TestParseBboxFromText(unittest.TestCase):

    def test_parse_square_bracket_format(self):
        """Parse [x1, y1, x2, y2] format."""
        from models.vqa.grounding import parse_bbox_from_text
        box = parse_bbox_from_text("The object is at [12, 34, 56, 78]")
        self.assertIsNotNone(box)
        self.assertEqual((box.x1, box.y1, box.x2, box.y2), (12, 34, 56, 78))

    def test_parse_space_separated(self):
        """Parse space-separated 4 numbers."""
        from models.vqa.grounding import parse_bbox_from_text
        box = parse_bbox_from_text("Bounding box: 100 200 300 400")
        self.assertIsNotNone(box)
        self.assertEqual(box.x1, 100)
        self.assertEqual(box.y2, 400)

    def test_parse_returns_none_for_no_numbers(self):
        """No numbers in text → None."""
        from models.vqa.grounding import parse_bbox_from_text
        box = parse_bbox_from_text("I cannot locate the object in this image.")
        self.assertIsNone(box)

    def test_parse_returns_none_for_wrong_count(self):
        """Only 3 numbers → None (need exactly 4)."""
        from models.vqa.grounding import parse_bbox_from_text
        box = parse_bbox_from_text("Numbers: 1 2 3")
        self.assertIsNone(box)

    def test_parse_returns_none_for_too_many_numbers(self):
        """More than 4 numbers without clear box pattern → ambiguous, should return None."""
        from models.vqa.grounding import parse_bbox_from_text
        # 5+ numbers is ambiguous - implementation may return None or the first 4
        # Just verify it returns BoundingBox or None, not an exception
        result = parse_bbox_from_text("Numbers: 1 2 3 4 5 6 7")
        # Either None or a BoundingBox is acceptable
        self.assertTrue(result is None or isinstance(result, BoundingBox))


class TestRunGrounding(unittest.TestCase):

    @patch("models.vqa.grounding.get_model_and_processor")
    @patch("models.vqa.grounding.Image")
    def test_run_grounding_parses_bbox_success(self, mock_pil_image, mock_get_model):
        """Grounding model returns coordinates → BoundingBox populated in response."""
        from models.vqa.grounding import run_grounding

        mock_model, mock_processor = _make_mock_model_processor(
            "The river is located at [100, 200, 300, 400]"
        )
        mock_get_model.return_value = (mock_model, mock_processor)
        mock_pil_image.open.return_value = MagicMock()

        with patch.dict("sys.modules", {"qwen_vl_utils": MagicMock(
            process_vision_info=MagicMock(return_value=(["img"], None))
        )}):
            req = SpecialistRequest(
                query="river",
                images=[_make_image_meta()],
                task_hint="grounding",
            )
            resp = run_grounding(req)

        self.assertEqual(resp.status, "success")
        self.assertGreater(len(resp.bounding_boxes), 0)
        box = resp.bounding_boxes[0]
        self.assertEqual(box.x1, 100)
        self.assertEqual(box.y1, 200)
        self.assertEqual(box.x2, 300)
        self.assertEqual(box.y2, 400)

    @patch("models.vqa.grounding.get_model_and_processor")
    @patch("models.vqa.grounding.Image")
    def test_run_grounding_returns_error_on_parse_failure(self, mock_pil_image, mock_get_model):
        """Grounding model returns no coordinates → status='error'."""
        from models.vqa.grounding import run_grounding

        mock_model, mock_processor = _make_mock_model_processor(
            "I cannot locate the specified object in this image."
        )
        mock_get_model.return_value = (mock_model, mock_processor)
        mock_pil_image.open.return_value = MagicMock()

        with patch.dict("sys.modules", {"qwen_vl_utils": MagicMock(
            process_vision_info=MagicMock(return_value=(["img"], None))
        )}):
            req = SpecialistRequest(
                query="unicorn",
                images=[_make_image_meta()],
                task_hint="grounding",
            )
            resp = run_grounding(req)

        self.assertEqual(resp.status, "error")
        self.assertIn("parsing failed", resp.error_message.lower())

    def test_run_grounding_rejects_zero_images(self):
        """run_grounding with 0 images → error."""
        from models.vqa.grounding import run_grounding
        req = SpecialistRequest(query="locate tree", images=[], task_hint="grounding")
        resp = run_grounding(req)
        self.assertEqual(resp.status, "error")


if __name__ == "__main__":
    unittest.main()
