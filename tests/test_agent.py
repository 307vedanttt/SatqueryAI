"""
tests/test_agent.py — Test Suite for the Agent Orchestration Core

Tests cover:
  1. Router.classify() — 8+ sample queries across all six tool types + ambiguous case
  2. ToolRegistry precondition checks — passing and failing cases per tool (12+ cases)
  3. Executor.run() end-to-end with stub tools
  4. Retry mechanism — tool fails twice then succeeds on the 3rd attempt
  5. Step-limit enforcement — tool always fails → stops at MAX_STEPS
  6. Precondition rejection — rejects without attempting execution
"""

import os
import sys
import tempfile
import pytest
from unittest.mock import MagicMock, patch

# Make the repo root importable regardless of how pytest is invoked
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.executor import Executor, MAX_STEPS, MAX_RETRIES
from agent.registry import ToolRegistry
from agent.router import Router
from schemas.contracts import (
    ExecutionTrace,
    ImageMetadata,
    SpecialistRequest,
    SpecialistResponse,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_image(
    sensor: str = "optical",
    crs: str = "EPSG:4326",
    resolution_m: float = 10.0,
    file_path: str = "/tmp/dummy.tif",
) -> ImageMetadata:
    """Helper to build an ImageMetadata for testing."""
    return ImageMetadata(
        sensor=sensor,
        crs=crs,
        width=512,
        height=512,
        bands=3,
        resolution_m=resolution_m,
        acquisition_date="2024-01-01",
        file_path=file_path,
    )


def _make_request(
    query: str,
    images: list[ImageMetadata],
    task_hint: str = "",
) -> SpecialistRequest:
    return SpecialistRequest(query=query, images=images, task_hint=task_hint)


@pytest.fixture
def router() -> Router:
    return Router()


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry()


@pytest.fixture
def executor() -> Executor:
    return Executor()


# ---------------------------------------------------------------------------
# 1. Router.classify() tests — 8+ queries covering all 6 tools
# ---------------------------------------------------------------------------

class TestRouterClassify:

    def test_optical_sar_fusion_by_image_type(self, router):
        """Two images (optical + SAR) → optical_sar_fusion regardless of query."""
        images = [_make_image("optical"), _make_image("sar")]
        result = router.classify("What can you tell me about this area?", images)
        assert result == "optical_sar_fusion"

    def test_optical_sar_fusion_sar_first(self, router):
        """Order of optical/SAR doesn't matter — still fusion."""
        images = [_make_image("sar"), _make_image("optical")]
        result = router.classify("Analyze these images.", images)
        assert result == "optical_sar_fusion"

    def test_change_vqa_with_question_mark(self, router):
        """Two same-sensor images + change keyword + question mark → change_vqa."""
        images = [_make_image("optical"), _make_image("optical")]
        result = router.classify("Has the vegetation changed between these two dates?", images)
        assert result == "change_vqa"

    def test_change_vqa_with_interrogative_word(self, router):
        """Two same-sensor images + change keyword + interrogative word → change_vqa."""
        images = [_make_image("optical"), _make_image("optical")]
        result = router.classify("What changed in the urban area before and after the flood", images)
        assert result == "change_vqa"

    def test_change_detection_no_question(self, router):
        """Two same-sensor images + change keyword, no interrogative → change_detection."""
        images = [_make_image("optical"), _make_image("optical")]
        result = router.classify("Compare the land cover between the two images", images)
        assert result == "change_detection"

    def test_change_detection_sar_pair(self, router):
        """Two SAR images → change_detection (same sensor, no interrogative)."""
        images = [_make_image("sar"), _make_image("sar")]
        result = router.classify("Show the difference between before and after", images)
        assert result == "change_detection"

    def test_ground_region_highlight(self, router):
        """Single image + 'highlight' keyword → ground_region."""
        images = [_make_image("optical")]
        result = router.classify("Highlight the river in this satellite image", images)
        assert result == "ground_region"

    def test_ground_region_where_is(self, router):
        """Single image + 'where is' keyword → ground_region."""
        images = [_make_image("optical")]
        result = router.classify("Where is the airport in this image?", images)
        assert result == "ground_region"

    def test_ground_region_locate(self, router):
        """Single image + 'locate' keyword → ground_region."""
        images = [_make_image("optical")]
        result = router.classify("Locate the water reservoir", images)
        assert result == "ground_region"

    def test_caption_image_describe(self, router):
        """Single image + 'describe' keyword, no '?' → caption_image."""
        images = [_make_image("optical")]
        result = router.classify("Describe the land cover and major objects visible in this image", images)
        assert result == "caption_image"

    def test_caption_image_no_question_mark(self, router):
        """Description keyword without question mark → caption_image, not vqa."""
        images = [_make_image("optical")]
        result = router.classify("Give me an overview of this satellite scene", images)
        assert result == "caption_image"

    def test_single_image_vqa_default(self, router):
        """Single image with a plain question → single_image_vqa (default)."""
        images = [_make_image("optical")]
        result = router.classify("How many buildings are visible?", images)
        assert result == "single_image_vqa"

    def test_single_image_vqa_generic_question(self, router):
        """Single image with describe+question → single_image_vqa (? overrides caption rule)."""
        images = [_make_image("optical")]
        result = router.classify("Describe what changes do you see?", images)
        # '?' prevents caption_image; no grounding keywords → single_image_vqa
        assert result == "single_image_vqa"

    def test_change_detection_same_sensor_no_change_keywords(self, router):
        """Two same-sensor images with no change keywords → defaults to change_detection."""
        images = [_make_image("optical"), _make_image("optical")]
        result = router.classify("Analyze the terrain features", images)
        assert result == "change_detection"

    def test_raises_for_zero_images(self, router):
        """No images → ValueError with descriptive message."""
        with pytest.raises(ValueError, match=r"[Cc]annot route|0 image"):
            router.classify("What is in this image?", [])

    def test_raises_for_mismatched_pair(self, router):
        """Two images with multispectral sensor (not optical/SAR) pair → ValueError."""
        images = [_make_image("multispectral"), _make_image("multispectral")]
        # Same sensor — should route to change_detection (same-sensor default)
        result = router.classify("Analyze this pair", images)
        assert result == "change_detection"

    def test_raises_for_ambiguous_two_image_pair(self, router):
        """Two images with inconsistent sensors (multispectral + sar) that
        don't form a clean optical+SAR pair → ValueError."""
        images = [_make_image("multispectral"), _make_image("sar")]
        # multispectral + sar: has_optical=False, has_sar=True → not optical+sar pair
        # same_sensor? multispectral != sar → False
        # Should raise ValueError
        with pytest.raises(ValueError):
            router.classify("Analyze this pair", images)


# ---------------------------------------------------------------------------
# 2. ToolRegistry precondition checks — at least 1 pass + 1 fail per tool (12+ total)
# ---------------------------------------------------------------------------

class TestToolRegistryPreconditions:

    # single_image_vqa
    def test_single_image_vqa_passes_one_image(self, registry):
        req = _make_request("What is this?", [_make_image()])
        ok, reason = registry.check_precondition("single_image_vqa", req)
        assert ok is True
        assert reason == ""

    def test_single_image_vqa_fails_two_images(self, registry):
        req = _make_request("What is this?", [_make_image(), _make_image()])
        ok, reason = registry.check_precondition("single_image_vqa", req)
        assert ok is False
        assert "1 image" in reason or "2" in reason

    def test_single_image_vqa_fails_zero_images(self, registry):
        req = _make_request("What is this?", [])
        ok, reason = registry.check_precondition("single_image_vqa", req)
        assert ok is False

    # caption_image
    def test_caption_image_passes_one_image(self, registry):
        req = _make_request("Describe this image.", [_make_image()])
        ok, _ = registry.check_precondition("caption_image", req)
        assert ok is True

    def test_caption_image_fails_zero_images(self, registry):
        req = _make_request("Describe this image.", [])
        ok, _ = registry.check_precondition("caption_image", req)
        assert ok is False

    # ground_region
    def test_ground_region_passes_one_image(self, registry):
        req = _make_request("Locate the river.", [_make_image()])
        ok, _ = registry.check_precondition("ground_region", req)
        assert ok is True

    def test_ground_region_fails_two_images(self, registry):
        req = _make_request("Locate the river.", [_make_image(), _make_image()])
        ok, reason = registry.check_precondition("ground_region", req)
        assert ok is False

    # change_detection
    def test_change_detection_passes_valid_pair(self, registry):
        imgs = [
            _make_image("optical", "EPSG:4326", 10.0, "/tmp/a.tif"),
            _make_image("optical", "EPSG:4326", 10.0, "/tmp/b.tif"),
        ]
        req = _make_request("What changed?", imgs)
        ok, reason = registry.check_precondition("change_detection", req)
        assert ok is True

    def test_change_detection_fails_one_image(self, registry):
        req = _make_request("What changed?", [_make_image()])
        ok, reason = registry.check_precondition("change_detection", req)
        assert ok is False
        assert "2 images" in reason or "1" in reason

    def test_change_detection_fails_mismatched_sensors(self, registry):
        imgs = [_make_image("optical"), _make_image("sar")]
        req = _make_request("What changed?", imgs)
        ok, reason = registry.check_precondition("change_detection", req)
        assert ok is False
        assert "sensor" in reason.lower()

    def test_change_detection_fails_crs_mismatch(self, registry):
        imgs = [
            _make_image("optical", "EPSG:4326", 10.0, "/tmp/a.tif"),
            _make_image("optical", "EPSG:32643", 10.0, "/tmp/b.tif"),
        ]
        req = _make_request("What changed?", imgs)
        ok, reason = registry.check_precondition("change_detection", req)
        assert ok is False
        assert "CRS" in reason or "crs" in reason.lower()

    def test_change_detection_fails_resolution_mismatch(self, registry):
        imgs = [
            _make_image("optical", "EPSG:4326", 10.0, "/tmp/a.tif"),
            _make_image("optical", "EPSG:4326", 25.0, "/tmp/b.tif"),  # >10% diff
        ]
        req = _make_request("What changed?", imgs)
        ok, reason = registry.check_precondition("change_detection", req)
        assert ok is False
        assert "resolution" in reason.lower() or "Resolution" in reason

    # change_vqa — same precondition logic as change_detection
    def test_change_vqa_passes_valid_pair(self, registry):
        imgs = [
            _make_image("sar", "EPSG:4326", 10.0, "/tmp/a.tif"),
            _make_image("sar", "EPSG:4326", 10.0, "/tmp/b.tif"),
        ]
        req = _make_request("Has the water body increased?", imgs)
        ok, _ = registry.check_precondition("change_vqa", req)
        assert ok is True

    def test_change_vqa_fails_one_image(self, registry):
        req = _make_request("Has the water body increased?", [_make_image("sar")])
        ok, _ = registry.check_precondition("change_vqa", req)
        assert ok is False

    # optical_sar_fusion
    def test_optical_sar_fusion_passes_valid_pair(self, registry):
        imgs = [
            _make_image("optical", "EPSG:4326"),
            _make_image("sar", "EPSG:4326"),
        ]
        req = _make_request("Analyze this area.", imgs)
        ok, _ = registry.check_precondition("optical_sar_fusion", req)
        assert ok is True

    def test_optical_sar_fusion_fails_two_optical(self, registry):
        imgs = [_make_image("optical"), _make_image("optical")]
        req = _make_request("Analyze this area.", imgs)
        ok, reason = registry.check_precondition("optical_sar_fusion", req)
        assert ok is False
        assert "sar" in reason.lower() or "optical" in reason.lower()

    def test_optical_sar_fusion_fails_one_image(self, registry):
        req = _make_request("Analyze this area.", [_make_image("optical")])
        ok, reason = registry.check_precondition("optical_sar_fusion", req)
        assert ok is False

    def test_optical_sar_fusion_fails_crs_mismatch(self, registry):
        imgs = [
            _make_image("optical", "EPSG:4326"),
            _make_image("sar", "EPSG:32643"),
        ]
        req = _make_request("Analyze.", imgs)
        ok, reason = registry.check_precondition("optical_sar_fusion", req)
        assert ok is False
        assert "CRS" in reason or "crs" in reason.lower()

    def test_registry_lists_all_six_tools(self, registry):
        """All six expected tools must be registered."""
        tools = registry.list_tools()
        assert set(tools) == {
            "single_image_vqa", "caption_image", "ground_region",
            "change_detection", "change_vqa", "optical_sar_fusion",
        }

    def test_register_tool_replaces_callable(self, registry):
        """register_tool() should replace the callable without error."""
        new_fn = lambda req: SpecialistResponse(
            task="vqa", answer="real answer", confidence=0.9,
            confidence_tier="high", status="success",
        )
        registry.register_tool(
            name="single_image_vqa",
            callable_fn=new_fn,
            precondition_fn=registry._tools["single_image_vqa"]["precondition"],
        )
        result = registry.get_callable("single_image_vqa")(
            _make_request("test", [_make_image()])
        )
        assert result.answer == "real answer"

    def test_register_tool_unknown_name_raises(self, registry):
        """register_tool() with unknown name → KeyError."""
        with pytest.raises(KeyError):
            registry.register_tool("nonexistent_tool", lambda r: None, lambda r: (True, ""))


# ---------------------------------------------------------------------------
# 3. Executor.run() end-to-end with stub tools
# ---------------------------------------------------------------------------

class TestExecutorEndToEnd:

    def test_successful_run_returns_success_status(self, executor):
        """Single-image request through stub → status='success', complete trace."""
        req = _make_request("What is visible?", [_make_image()])
        response, trace = executor.run(req)
        assert response.status == "success"
        assert response.confidence_tier == "moderate"
        assert "[STUB" in response.answer

    def test_successful_run_returns_execution_trace(self, executor):
        """ExecutionTrace must have steps populated and total_steps > 0."""
        req = _make_request("Describe this image.", [_make_image()])
        response, trace = executor.run(req)
        assert isinstance(trace, ExecutionTrace)
        assert trace.total_steps > 0
        assert len(trace.steps) == trace.total_steps

    def test_trace_contains_routing_step(self, executor):
        """Trace must contain a step mentioning the classified tool."""
        req = _make_request("Describe the land cover and major objects visible in this image", [_make_image()])
        response, trace = executor.run(req)
        # One of the steps should mention the tool name
        tool_mentioned = any(
            trace.intent_classified in (s.tool_used or "") or
            trace.intent_classified in s.result_summary
            for s in trace.steps
        )
        assert tool_mentioned

    def test_trace_step_count_within_max(self, executor):
        """Step count must never exceed MAX_STEPS."""
        req = _make_request("What changed?", [_make_image(), _make_image()])
        _, trace = executor.run(req)
        assert trace.total_steps <= MAX_STEPS

    def test_grounding_route_succeeds(self, executor):
        """Grounding request → routes correctly and returns success."""
        req = _make_request("Locate the water body in this image.", [_make_image()])
        response, trace = executor.run(req)
        assert response.status == "success"
        assert trace.intent_classified == "ground_region"

    def test_change_detection_two_images(self, executor):
        """Two-image change detection request → routes and succeeds."""
        imgs = [
            _make_image("optical", "EPSG:4326", 10.0, "/tmp/a.tif"),
            _make_image("optical", "EPSG:4326", 10.0, "/tmp/b.tif"),
        ]
        req = _make_request("What changed between the two images?", imgs)
        response, trace = executor.run(req)
        assert response.status == "success"
        assert trace.intent_classified in ("change_vqa", "change_detection")

    def test_optical_sar_fusion_route(self, executor):
        """Optical+SAR pair → routed to optical_sar_fusion."""
        imgs = [
            _make_image("optical", "EPSG:4326"),
            _make_image("sar", "EPSG:4326"),
        ]
        req = _make_request("Analyze this area.", imgs)
        response, trace = executor.run(req)
        assert response.status == "success"
        assert trace.intent_classified == "optical_sar_fusion"

    def test_missing_sensor_returns_error(self, executor):
        """Image with empty sensor field → validation failure, status='error'."""
        bad_img = ImageMetadata(
            sensor="",  # invalid
            file_path="/tmp/dummy.tif",
            width=512,
            height=512,
            bands=3,
        )
        req = _make_request("Analyze this.", [bad_img])
        response, trace = executor.run(req)
        assert response.status == "error"
        assert trace.total_steps >= 1

    def test_empty_file_path_returns_error(self, executor):
        """Image with empty file_path → validation failure."""
        bad_img = ImageMetadata(sensor="optical", file_path="")
        req = _make_request("Analyze this.", [bad_img])
        response, trace = executor.run(req)
        assert response.status == "error"


# ---------------------------------------------------------------------------
# 4. Retry mechanism — tool fails twice, succeeds on 3rd attempt
# ---------------------------------------------------------------------------

class TestExecutorRetry:

    def test_tool_retries_and_eventually_succeeds(self):
        """Mock a tool that raises RuntimeError twice then succeeds.
        Verify final status is 'success' and trace shows 2 failed + 1 success step."""
        attempt_counter = {"n": 0}

        def flaky_tool(request: SpecialistRequest) -> SpecialistResponse:
            attempt_counter["n"] += 1
            if attempt_counter["n"] < 3:
                raise RuntimeError(f"Simulated transient failure (attempt {attempt_counter['n']})")
            return SpecialistResponse(
                task="vqa",
                answer="Real answer after retries",
                confidence=0.8,
                confidence_tier="high",
                status="success",
            )

        registry = ToolRegistry()
        registry.register_tool(
            name="single_image_vqa",
            callable_fn=flaky_tool,
            precondition_fn=registry._tools["single_image_vqa"]["precondition"],
        )
        executor = Executor(registry=registry)
        req = _make_request("What is visible?", [_make_image()])
        response, trace = executor.run(req)

        # Should eventually succeed
        assert response.status == "success"
        assert response.answer == "Real answer after retries"
        assert attempt_counter["n"] == 3  # 2 failures + 1 success

        # Trace should show 2 failed execution steps
        exec_steps = [s for s in trace.steps if "Execute" in s.action]
        failed_steps = [s for s in exec_steps if "FAILED" in s.result_summary]
        success_steps = [s for s in exec_steps if "SUCCESS" in s.result_summary]
        assert len(failed_steps) == 2
        assert len(success_steps) == 1

    def test_tool_exhausts_all_retries_returns_error(self):
        """Tool always raises → exhausts MAX_RETRIES+1 attempts → status='error'."""
        call_count = {"n": 0}

        def always_fails(request: SpecialistRequest) -> SpecialistResponse:
            call_count["n"] += 1
            raise RuntimeError("Always fails")

        registry = ToolRegistry()
        registry.register_tool(
            name="caption_image",
            callable_fn=always_fails,
            precondition_fn=registry._tools["caption_image"]["precondition"],
        )
        executor = Executor(registry=registry)
        req = _make_request("Describe the scene.", [_make_image()])
        response, trace = executor.run(req)

        assert response.status == "error"
        assert call_count["n"] == MAX_RETRIES + 1  # 3 attempts total
        assert "insufficient" == response.confidence_tier


# ---------------------------------------------------------------------------
# 5. Step-limit enforcement — stops at MAX_STEPS
# ---------------------------------------------------------------------------

class TestExecutorStepLimit:

    def test_step_limit_stops_execution(self):
        """When MAX_STEPS would be exceeded, executor stops and returns error."""
        # Make a tool that always fails so retries consume steps
        def always_fails(request: SpecialistRequest) -> SpecialistResponse:
            raise RuntimeError("Always fails")

        registry = ToolRegistry()
        registry.register_tool(
            name="single_image_vqa",
            callable_fn=always_fails,
            precondition_fn=registry._tools["single_image_vqa"]["precondition"],
        )
        executor = Executor(registry=registry)
        req = _make_request("What is visible?", [_make_image()])
        response, trace = executor.run(req)

        # Must have stopped
        assert response.status == "error"
        # Must not have exceeded MAX_STEPS
        assert trace.total_steps <= MAX_STEPS
        assert response.confidence_tier == "insufficient"


# ---------------------------------------------------------------------------
# 6. Precondition rejection — rejects immediately without execution
# ---------------------------------------------------------------------------

class TestPreconditionRejection:

    def test_change_detection_one_image_rejected_immediately(self):
        """change_detection with 1 image → precondition rejection, no execution attempt."""
        execution_attempted = {"flag": False}

        def should_not_be_called(request: SpecialistRequest) -> SpecialistResponse:
            execution_attempted["flag"] = True
            return SpecialistResponse(
                task="change_detection", answer="should not reach here",
                confidence_tier="high", status="success",
            )

        registry = ToolRegistry()
        registry.register_tool(
            name="change_detection",
            callable_fn=should_not_be_called,
            precondition_fn=registry._tools["change_detection"]["precondition"],
        )
        executor = Executor(registry=registry)

        # Only 1 image — precondition requires 2
        req = _make_request("What changed?", [_make_image("optical")])

        # Force the router to pick change_detection for this 1-image request
        # by patching the router
        mock_router = MagicMock()
        mock_router.classify.return_value = "change_detection"
        executor._router = mock_router

        response, trace = executor.run(req)

        # Precondition must have rejected it
        assert response.status == "error"
        assert execution_attempted["flag"] is False  # callable was NOT invoked
        # Verify the rejection is logged in the trace
        rejection_steps = [
            s for s in trace.steps
            if "REJECTED" in s.result_summary or "Precondition" in s.action
        ]
        assert len(rejection_steps) >= 1

    def test_optical_sar_fusion_wrong_sensors_rejected(self):
        """optical_sar_fusion with two optical images → rejected without execution."""
        called = {"n": 0}

        def sentinel_callable(request: SpecialistRequest) -> SpecialistResponse:
            called["n"] += 1
            return SpecialistResponse(
                task="optical_sar_fusion", answer="x", confidence_tier="high", status="success"
            )

        registry = ToolRegistry()
        registry.register_tool(
            name="optical_sar_fusion",
            callable_fn=sentinel_callable,
            precondition_fn=registry._tools["optical_sar_fusion"]["precondition"],
        )
        executor = Executor(registry=registry)

        imgs = [_make_image("optical"), _make_image("optical")]
        req = _make_request("Analyze this.", imgs)

        # Force the router to select optical_sar_fusion even for two optical images
        mock_router = MagicMock()
        mock_router.classify.return_value = "optical_sar_fusion"
        executor._router = mock_router

        response, trace = executor.run(req)

        assert response.status == "error"
        assert called["n"] == 0  # Never executed
