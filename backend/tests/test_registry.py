import pytest
from app.registry.registry import SpecialistRegistry
from app.registry.schemas import ToolSpec
from app.specialists.base import Specialist
from app.models.schemas import SpecialistRequest, SpecialistResult
from app.core.exceptions import InvalidToolRequestError, NoSpecialistAvailableError

class DummySpecialist(Specialist):
    @property
    def name(self) -> str:
        return "dummy_specialist"

    @property
    def capabilities(self) -> list[str]:
        return ["TEST_CAPABILITY"]

    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        return SpecialistResult(
            specialist=self.name,
            model_name="dummy-v1",
            task="test",
            status="success",
            answer="Dummy answer",
            latency=0.5,
            warnings=["Test warning"]
        )

def get_dummy_spec(name="dummy_specialist", status="available") -> ToolSpec:
    return ToolSpec(
        name=name,
        version="1.0.0",
        display_name="Dummy Specialist",
        description="A dummy specialist for testing",
        capabilities=["TEST_CAPABILITY"],
        supported_input_configurations=["SINGLE_OPTICAL"],
        supported_intents=["VQA"],
        provider="mock",
        model_status="mock",
        availability_status=status
    )

def test_registration_and_lookup():
    registry = SpecialistRegistry()
    spec = get_dummy_spec()
    registry.register(spec, DummySpecialist, is_lazy=True)
    
    retrieved_spec = registry.get_spec("dummy_specialist")
    assert retrieved_spec.name == "dummy_specialist"
    
    impl = registry.get_specialist("dummy_specialist")
    assert isinstance(impl, DummySpecialist)

def test_duplicate_registration(caplog):
    registry = SpecialistRegistry()
    spec = get_dummy_spec()
    registry.register(spec, DummySpecialist, is_lazy=True)
    # Registering again
    registry.register(spec, DummySpecialist, is_lazy=True)
    assert "specialist_duplicate_registration" in caplog.text

def test_unsupported_task():
    registry = SpecialistRegistry()
    # Missing capability for the intent
    found = registry.find_for_config_and_intent("SINGLE_OPTICAL", "UNKNOWN_INTENT", ["TEST_CAPABILITY"])
    assert found is None

def test_unavailable_model():
    registry = SpecialistRegistry()
    spec = get_dummy_spec(status="unavailable")
    registry.register(spec, DummySpecialist, is_lazy=True)
    
    with pytest.raises(NoSpecialistAvailableError):
        registry.get_specialist("dummy_specialist")

def test_lazy_loading_and_unload():
    registry = SpecialistRegistry()
    spec = get_dummy_spec()
    
    # Track instantiation
    loaded = False
    def factory():
        nonlocal loaded
        loaded = True
        return DummySpecialist()
        
    registry.register(spec, factory, is_lazy=True)
    assert not loaded
    
    impl = registry.get_specialist("dummy_specialist")
    assert loaded
    assert isinstance(impl, DummySpecialist)
    
    registry.unload_specialist("dummy_specialist")
    assert "dummy_specialist" not in registry._impls

@pytest.mark.asyncio
async def test_result_schema():
    specialist = DummySpecialist()
    req = SpecialistRequest(
        request_id="123",
        specialist_name="dummy_specialist",
        input_configuration="SINGLE_OPTICAL",
        intent="VQA",
        file_ids=[],
        file_paths=[],
        metadata=[],
        query="test"
    )
    result = await specialist.execute(req)
    # Schema validation
    assert result.specialist == "dummy_specialist"
    assert result.model_name == "dummy-v1"
    assert result.task == "test"
    assert result.latency == 0.5
    assert "Test warning" in result.warnings

def test_specialist_discovery():
    registry = SpecialistRegistry()
    spec1 = get_dummy_spec("spec1")
    spec2 = get_dummy_spec("spec2")
    spec2.capabilities.append("ANOTHER_CAP")
    
    registry.register(spec1, DummySpecialist, is_lazy=True)
    registry.register(spec2, DummySpecialist, is_lazy=True)
    
    found = registry.find_for_config_and_intent("SINGLE_OPTICAL", "VQA", ["ANOTHER_CAP"])
    assert found is not None
    assert found.name == "spec2"
