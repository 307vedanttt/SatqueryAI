"""
SatQuery AI — Backend Tests: Router

Tests for input configuration classification and intent classification.
"""

import pytest

from app.models.schemas import ImageMetadata, InputConfiguration, QueryIntent
from app.router.classifier import classify_input_configuration
from app.router.execution_graph import ROUTING_TABLE, ExecutionGraph
from app.router.planner import classify_intent
from app.registry.registry import SpecialistRegistry


def _optical(acquisition_date=None) -> ImageMetadata:
    return ImageMetadata(
        filename="optical.tif",
        is_geotiff=True,
        crs="EPSG:4326",
        resolution=(10.0, 10.0),
        bounds=(0.0, 0.0, 1.0, 1.0),
        image_type="optical",
        acquisition_date=acquisition_date,
    )


def _sar() -> ImageMetadata:
    return ImageMetadata(
        filename="sar.tif",
        is_geotiff=True,
        crs="EPSG:4326",
        resolution=(10.0, 10.0),
        bounds=(0.0, 0.0, 1.0, 1.0),
        image_type="sar",
    )


# ---- Configuration Classifier Tests -------------------------------------

class TestInputClassifier:
    def test_single_optical(self):
        result = classify_input_configuration([_optical()])
        assert result == InputConfiguration.SINGLE_OPTICAL

    def test_single_sar(self):
        result = classify_input_configuration([_sar()])
        assert result == InputConfiguration.SINGLE_SAR

    def test_optical_sar_pair(self):
        result = classify_input_configuration([_optical(), _sar()])
        assert result == InputConfiguration.OPTICAL_SAR_PAIR

    def test_bitemporal_with_dates(self):
        img1 = _optical(acquisition_date="2024-01-01")
        img2 = _optical(acquisition_date="2024-06-01")
        result = classify_input_configuration([img1, img2])
        assert result == InputConfiguration.BI_TEMPORAL

    def test_empty_returns_unknown(self):
        result = classify_input_configuration([])
        assert result == InputConfiguration.UNKNOWN

    def test_three_images_returns_unknown(self):
        result = classify_input_configuration([_optical(), _optical(), _optical()])
        assert result == InputConfiguration.UNKNOWN


# ---- Intent Classifier Tests --------------------------------------------

class TestIntentClassifier:
    def test_scene_description(self):
        result = classify_intent("Describe what you see in this image.", InputConfiguration.SINGLE_OPTICAL)
        assert result.type == QueryIntent.SCENE_DESCRIPTION
        assert result.confidence > 0.5

    def test_change_description(self):
        result = classify_intent("What changed between these two images?", InputConfiguration.BI_TEMPORAL)
        assert result.type == QueryIntent.CHANGE_DESCRIPTION
        assert result.confidence > 0.7

    def test_water_analysis(self):
        result = classify_intent("Show me all the water bodies in this image.", InputConfiguration.SINGLE_OPTICAL)
        assert result.type == QueryIntent.WATER_ANALYSIS

    def test_built_up_analysis(self):
        result = classify_intent("Identify built-up regions and urban areas.", InputConfiguration.SINGLE_OPTICAL)
        assert result.type == QueryIntent.BUILT_UP_ANALYSIS

    def test_grounding_query(self):
        result = classify_intent("Where is the lake in this image?", InputConfiguration.SINGLE_OPTICAL)
        assert result.type == QueryIntent.GROUNDING

    def test_bitemporal_config_overrides_to_change(self):
        # Generic query + bi-temporal config → should default to CHANGE_DESCRIPTION
        result = classify_intent("Analyze this image.", InputConfiguration.BI_TEMPORAL)
        assert result.type == QueryIntent.CHANGE_DESCRIPTION

    def test_optical_sar_config_defaults(self):
        result = classify_intent("Tell me about this image.", InputConfiguration.OPTICAL_SAR_PAIR)
        assert result.type in (QueryIntent.OPTICAL_SAR_ANALYSIS, QueryIntent.SCENE_DESCRIPTION)

    def test_intent_has_required_capabilities(self):
        result = classify_intent("Describe the land cover.", InputConfiguration.SINGLE_OPTICAL)
        assert isinstance(result.required_capabilities, list)
        assert len(result.required_capabilities) > 0


# ---- Execution Graph Tests ----------------------------------------------

class TestExecutionGraph:
    @pytest.fixture
    def registry(self):
        r = SpecialistRegistry()
        r.bootstrap()
        return r

    def test_single_optical_scene_description_routes_correctly(self, registry):
        from app.models.schemas import IntentResult
        graph = ExecutionGraph(registry)
        intent = IntentResult(
            type=QueryIntent.SCENE_DESCRIPTION,
            confidence=0.85,
            required_capabilities=["single_image_analysis"],
        )
        plan = graph.plan(InputConfiguration.SINGLE_OPTICAL, intent)
        assert plan.specialist == "mock_single_image"
        assert len(plan.execution_steps) > 0

    def test_bitemporal_routes_to_change_detection(self, registry):
        from app.models.schemas import IntentResult
        graph = ExecutionGraph(registry)
        intent = IntentResult(
            type=QueryIntent.CHANGE_DESCRIPTION,
            confidence=0.88,
            required_capabilities=["change_detection"],
        )
        plan = graph.plan(InputConfiguration.BI_TEMPORAL, intent)
        assert plan.specialist == "mock_change_detection"

    def test_optical_sar_pair_routes_correctly(self, registry):
        from app.models.schemas import IntentResult
        graph = ExecutionGraph(registry)
        intent = IntentResult(
            type=QueryIntent.OPTICAL_SAR_ANALYSIS,
            confidence=0.84,
            required_capabilities=["optical_sar_fusion"],
        )
        plan = graph.plan(InputConfiguration.OPTICAL_SAR_PAIR, intent)
        assert plan.specialist == "mock_optical_sar"

    def test_grounding_routes_to_grounding_specialist(self, registry):
        from app.models.schemas import IntentResult
        graph = ExecutionGraph(registry)
        intent = IntentResult(
            type=QueryIntent.GROUNDING,
            confidence=0.85,
            required_capabilities=["grounding"],
        )
        plan = graph.plan(InputConfiguration.SINGLE_OPTICAL, intent)
        assert plan.specialist == "mock_grounding"

    def test_routing_table_covers_all_configs(self):
        """Ensure every InputConfiguration has at least one routing entry."""
        covered = {k[0] for k in ROUTING_TABLE.keys()}
        important = {"SINGLE_OPTICAL", "SINGLE_SAR", "BI_TEMPORAL", "OPTICAL_SAR_PAIR"}
        assert important.issubset(covered)
