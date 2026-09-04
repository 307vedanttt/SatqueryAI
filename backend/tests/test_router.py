import pytest
from app.router.router import BoundedQueryRouter, RouterResult
from app.registry.registry import SpecialistRegistry
from app.registry.schemas import ToolSpec
from app.models.schemas import ImageMetadata
from app.specialists.base import Specialist

class DummySpecialist(Specialist):
    @property
    def name(self) -> str:
        return "mock_single_image"
    @property
    def capabilities(self) -> list[str]:
        return ["single_image_analysis"]
    async def execute(self, request):
        pass

@pytest.fixture
def registry():
    reg = SpecialistRegistry()
    reg.bootstrap()
    return reg

@pytest.fixture
def router(registry):
    return BoundedQueryRouter(registry)

@pytest.fixture(autouse=True)
def mock_validate_pair(monkeypatch):
    from app.ingestion.alignment import PairValidationResult
    monkeypatch.setattr(
        "app.router.classifier.validate_pair",
        lambda img1, img2: PairValidationResult(valid=True)
    )

def get_metadata(config="single"):
    if config == "single":
        return [ImageMetadata(filename="test.tif", is_geotiff=True)]
    elif config == "optical_sar":
        m1 = ImageMetadata(filename="opt.tif", is_geotiff=True, image_type="optical")
        m2 = ImageMetadata(filename="sar.tif", is_geotiff=True, image_type="sar")
        return [m1, m2]
    elif config == "bitemporal":
        m1 = ImageMetadata(filename="opt1.tif", is_geotiff=True, image_type="optical")
        m2 = ImageMetadata(filename="opt2.tif", is_geotiff=True, image_type="optical")
        return [m1, m2]
    return []

def test_single_vqa(router):
    res = router.route("how many buildings?", get_metadata("single"))
    assert res.intent == "VQA"
    assert res.configuration == "SINGLE_OPTICAL"
    assert res.selected_specialist == "mock_single_image"

def test_caption(router):
    res = router.route("describe this image", get_metadata("single"))
    assert res.intent == "SCENE_DESCRIPTION"
    assert res.configuration == "SINGLE_OPTICAL"
    assert res.selected_specialist == "mock_single_image"

def test_grounding(router):
    res = router.route("where is the road?", get_metadata("single"))
    assert res.intent == "GROUNDING"
    assert res.selected_specialist == "mock_grounding"

def test_optical_sar(router):
    res = router.route("combine and analyze", get_metadata("optical_sar"))
    assert res.configuration == "OPTICAL_SAR_PAIR"
    assert res.selected_specialist == "mock_optical_sar"

def test_bi_temporal_change(router):
    res = router.route("what changed?", get_metadata("bitemporal"))
    assert res.configuration == "BI_TEMPORAL"
    assert res.intent == "CHANGE_DESCRIPTION"
    assert res.selected_specialist == "mock_change_detection"

def test_unsupported_query(router):
    # Depending on rules, it might fall back to SCENE_DESCRIPTION or UNKNOWN.
    # We modified the router to reject if intent == "UNKNOWN".
    # Let's mock classify_intent to return UNKNOWN to test rejection.
    from unittest.mock import patch
    from app.models.schemas import IntentResult, QueryIntent
    with patch("app.router.router.classify_intent") as mock_intent:
        mock_intent.return_value = IntentResult(type=QueryIntent.UNKNOWN, confidence=1.0, required_capabilities=[])
        with pytest.raises(ValueError, match="Unsupported query intent"):
            router.route("do my taxes", get_metadata("single"))

def test_unavailable_specialist(router):
    # Mock check_availability to return unavailable
    from unittest.mock import patch
    with patch.object(router.registry, "check_availability", return_value="unavailable"):
        with pytest.raises(RuntimeError, match="currently unavailable"):
            router.route("describe", get_metadata("single"))

def test_invalid_input(router):
    with pytest.raises(ValueError, match="empty"):
        router.route("", get_metadata("single"))
        
    with pytest.raises(ValueError, match="metadata"):
        router.route("describe", [])
