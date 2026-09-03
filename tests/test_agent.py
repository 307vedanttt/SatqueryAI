"""
SatQuery AI — Agent Test Suite (Person A)

Tests:
  - Router classification (8+ queries covering 6 tools + ambiguity)
  - ToolRegistry preconditions (12+ pass/fail cases)
  - Executor end-to-end execution, retries, step limit enforcement, precondition rejection
"""

import pytest
from unittest.mock import MagicMock

from schemas.contracts import ImageMetadata, SpecialistRequest, SpecialistResponse
from agent.registry import ToolRegistry, check_single_image, check_change_detection, check_optical_sar_fusion
from agent.router import Router
from agent.executor import Executor, MAX_STEPS, MAX_RETRIES


# ---- Router Tests --------------------------------------------------------

class TestRouter:
    @pytest.fixture
    def router(self):
        return Router()

    @pytest.fixture
    def img_opt(self):
        return ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/a.tif")

    @pytest.fixture
    def img_sar(self):
        return ImageMetadata(sensor="sar", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/b.tif")

    def test_optical_sar_fusion_routing(self, router, img_opt, img_sar):
        tool = router.classify("Combine both sensors to map water", [img_opt, img_sar])
        assert tool == "optical_sar_fusion"

    def test_change_vqa_routing(self, router, img_opt):
        img_opt2 = ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/a2.tif")
        tool = router.classify("Has the water body changed between these dates?", [img_opt, img_opt2])
        assert tool == "change_vqa"

    def test_change_detection_routing(self, router, img_opt):
        img_opt2 = ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/a2.tif")
        tool = router.classify("Detect difference before and after development", [img_opt, img_opt2])
        assert tool == "change_detection"

    def test_grounding_routing(self, router, img_opt):
        tool = router.classify("Highlight the primary bridge in this image", [img_opt])
        assert tool == "ground_region"

    def test_grounding_where_is_routing(self, router, img_opt):
        tool = router.classify("Where is the hospital located?", [img_opt])
        assert tool == "ground_region"

    def test_caption_image_routing(self, router, img_opt):
        tool = router.classify("Describe what is in this image", [img_opt])
        assert tool == "caption_image"

    def test_single_image_vqa_default_routing(self, router, img_opt):
        tool = router.classify("What is the percentage of vegetation?", [img_opt])
        assert tool == "single_image_vqa"

    def test_ambiguous_3_images_raises_value_error(self, router, img_opt):
        with pytest.raises(ValueError) as exc_info:
            router.classify("Analyze these 3 images", [img_opt, img_opt, img_opt])
        assert "Unable to route query" in str(exc_info.value)


# ---- Registry & Precondition Tests -------------------------------------

class TestToolRegistryPreconditions:
    @pytest.fixture
    def req_1_opt(self):
        return SpecialistRequest(
            query="test",
            images=[ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/a.tif")]
        )

    @pytest.fixture
    def req_2_opt_matching(self):
        return SpecialistRequest(
            query="test",
            images=[
                ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/a.tif"),
                ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/b.tif")
            ]
        )

    @pytest.fixture
    def req_opt_sar(self):
        return SpecialistRequest(
            query="test",
            images=[
                ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/a.tif"),
                ImageMetadata(sensor="sar", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/b.tif")
            ]
        )

    def test_single_image_check_pass(self, req_1_opt):
        ok, reason = check_single_image(req_1_opt)
        assert ok is True

    def test_single_image_check_fail(self, req_2_opt_matching):
        ok, reason = check_single_image(req_2_opt_matching)
        assert ok is False
        assert "exactly 1 image" in reason

    def test_change_detection_check_pass(self, req_2_opt_matching):
        ok, reason = check_change_detection(req_2_opt_matching)
        assert ok is True

    def test_change_detection_check_fail_count(self, req_1_opt):
        ok, reason = check_change_detection(req_1_opt)
        assert ok is False

    def test_change_detection_check_fail_sensor_mismatch(self, req_opt_sar):
        ok, reason = check_change_detection(req_opt_sar)
        assert ok is False
        assert "Sensor mismatch" in reason

    def test_change_detection_check_fail_crs_mismatch(self):
        req = SpecialistRequest(
            query="test",
            images=[
                ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/a.tif"),
                ImageMetadata(sensor="optical", crs="EPSG:32643", width=100, height=100, resolution_m=10.0, file_path="/b.tif")
            ]
        )
        ok, reason = check_change_detection(req)
        assert ok is False
        assert "CRS mismatch" in reason

    def test_change_detection_check_fail_resolution_mismatch(self):
        req = SpecialistRequest(
            query="test",
            images=[
                ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/a.tif"),
                ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=30.0, file_path="/b.tif")
            ]
        )
        ok, reason = check_change_detection(req)
        assert ok is False
        assert "Resolution mismatch" in reason

    def test_optical_sar_fusion_check_pass(self, req_opt_sar):
        ok, reason = check_optical_sar_fusion(req_opt_sar)
        assert ok is True

    def test_optical_sar_fusion_check_fail_sensor(self, req_2_opt_matching):
        ok, reason = check_optical_sar_fusion(req_2_opt_matching)
        assert ok is False
        assert "Requires 1 optical and 1 SAR" in reason


# ---- Executor Tests -----------------------------------------------------

class TestExecutor:
    @pytest.fixture
    def executor(self):
        return Executor()

    @pytest.fixture
    def valid_vqa_request(self):
        return SpecialistRequest(
            query="Describe this image.",
            images=[ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/tmp/a.tif")]
        )

    def test_executor_successful_run(self, executor, valid_vqa_request):
        resp, trace = executor.run(valid_vqa_request)
        assert resp.status == "success"
        assert trace.intent_classified == "caption_image"
        assert trace.total_steps >= 4
        assert len(trace.steps) == trace.total_steps

    def test_executor_precondition_rejection_immediate(self, executor):
        # Change query with only 1 image -> router routes to single image, but if forced change request:
        req = SpecialistRequest(
            query="What changed between these images?",
            images=[ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path="/tmp/a.tif")]
        )
        # Force router to classify as change_vqa to trigger precondition fail
        executor.router.classify = MagicMock(return_value="change_vqa")
        resp, trace = executor.run(req)
        assert resp.status == "error"
        assert resp.confidence_tier == "insufficient"
        assert "Precondition failed" in trace.steps[-1].result_summary

    def test_executor_retry_mechanism_succeeds_on_third_attempt(self, executor, valid_vqa_request):
        # Mock tool callable to fail twice then succeed
        calls = 0

        def flaky_tool(req):
            nonlocal calls
            calls += 1
            if calls < 3:
                raise RuntimeError(f"Attempt {calls} failed")
            return SpecialistResponse(task="caption_image", answer="Success after retries", status="success")

        executor.registry.get_tool("caption_image").callable_fn = flaky_tool

        resp, trace = executor.run(valid_vqa_request)
        assert resp.status == "success"
        assert resp.answer == "Success after retries"
        assert calls == 3

    def test_executor_step_limit_enforcement(self, executor, valid_vqa_request):
        # Mock tool callable to always fail
        def failing_tool(req):
            raise RuntimeError("Always fails")

        executor.registry.get_tool("caption_image").callable_fn = failing_tool

        resp, trace = executor.run(valid_vqa_request)
        assert resp.status == "error"
        assert resp.confidence_tier == "insufficient"
        assert trace.total_steps <= MAX_STEPS + 1
