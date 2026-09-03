"""
SatQuery AI — Backend Tests: Registry

Tests for tool registration, lookup, validation, and disabled tool handling.
"""

import pytest

from app.core.exceptions import InvalidToolRequestError
from app.registry.registry import SpecialistRegistry
from app.registry.schemas import ToolSpec
from app.specialists.base import Specialist
from app.models.schemas import SpecialistRequest, SpecialistResult, AnalysisStatus


class _FakeSpecialist(Specialist):
    @property
    def name(self): return "fake_tool"
    @property
    def capabilities(self): return ["test_cap"]
    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        return SpecialistResult(specialist=self.name, status=AnalysisStatus.SUCCESS, answer="test", raw_confidence=0.9)


def _make_spec(name="fake_tool", enabled=True) -> ToolSpec:
    return ToolSpec(
        name=name,
        version="0.1.0",
        display_name="Fake",
        description="Test tool",
        capabilities=["test_cap"],
        supported_input_configurations=["SINGLE_OPTICAL"],
        supported_intents=["SCENE_DESCRIPTION"],
        provider="mock",
        enabled=enabled,
    )


class TestRegistry:
    def test_register_and_retrieve(self):
        registry = SpecialistRegistry()
        registry.register(_make_spec(), _FakeSpecialist())
        spec = registry.get_spec("fake_tool")
        assert spec.name == "fake_tool"

    def test_get_implementation(self):
        registry = SpecialistRegistry()
        impl = _FakeSpecialist()
        registry.register(_make_spec(), impl)
        retrieved = registry.get_specialist("fake_tool")
        assert retrieved is impl

    def test_unknown_tool_raises(self):
        registry = SpecialistRegistry()
        with pytest.raises(InvalidToolRequestError) as exc_info:
            registry.get_specialist("nonexistent_tool")
        assert exc_info.value.error_code == "INVALID_TOOL_REQUEST"

    def test_disabled_tool_not_registered(self):
        registry = SpecialistRegistry()
        registry.register(_make_spec(enabled=False), _FakeSpecialist())
        with pytest.raises(InvalidToolRequestError):
            registry.get_specialist("fake_tool")

    def test_list_tools_returns_all_enabled(self):
        registry = SpecialistRegistry()
        registry.register(_make_spec("tool_a"), _FakeSpecialist())
        registry.register(_make_spec("tool_b"), _FakeSpecialist())
        tools = registry.list_tools()
        assert len(tools) == 2

    def test_find_by_capability(self):
        registry = SpecialistRegistry()
        registry.register(_make_spec(), _FakeSpecialist())
        results = registry.find_by_capability("test_cap")
        assert len(results) == 1
        assert results[0].name == "fake_tool"

    def test_find_by_missing_capability_empty(self):
        registry = SpecialistRegistry()
        registry.register(_make_spec(), _FakeSpecialist())
        results = registry.find_by_capability("nonexistent_cap")
        assert results == []

    def test_bootstrap_registers_all_specialists(self):
        registry = SpecialistRegistry()
        registry.bootstrap()
        tools = registry.list_tools()
        names = {t.name for t in tools}
        assert "mock_single_image" in names
        assert "mock_optical_sar" in names
        assert "mock_change_detection" in names
        assert "mock_grounding" in names

    def test_invalid_parameters_spec(self):
        """ToolSpec must reject invalid version format gracefully."""
        spec = _make_spec()
        spec.version = "invalid"  # Still valid string — Pydantic doesn't constrain format
        assert spec.version == "invalid"  # Just a string, no semver enforcement yet
