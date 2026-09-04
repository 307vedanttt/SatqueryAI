"""
SatQuery AI — Specialist Registry

The registry is the ONLY source of allowed tools/specialists.
The router CANNOT select tools not registered here.
Invalid tool requests fail immediately with a typed error.

Bootstrap registers all built-in specialists at startup.
Adding a new specialist: implement Specialist, register ToolSpec, add to bootstrap().
"""

from app.core.exceptions import InvalidToolRequestError, NoSpecialistAvailableError
from app.core.logging import get_logger
from app.registry.capabilities import Capability
from app.registry.schemas import ToolSpec
from app.specialists.base import Specialist

logger = get_logger(__name__)


class SpecialistRegistry:
    """
    Central registry for all tool/specialist specs and their implementations.
    
    Two parallel stores:
      _specs  : name → ToolSpec  (metadata, for routing decisions)
      _impls  : name → Specialist (actual implementation)
    """

    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}
        self._impls: dict[str, Specialist] = {}
        self._factories: dict[str, Any] = {}

    def register(self, spec: ToolSpec, implementation_or_factory: Any, is_lazy: bool = False) -> None:
        """Register a specialist with its spec and either an implementation instance or a factory for lazy loading."""
        if not spec.enabled:
            logger.info("specialist_disabled", name=spec.name)
            return

        # Check for duplicate
        if spec.name in self._specs:
            logger.warning("specialist_duplicate_registration", name=spec.name)
            
        self._specs[spec.name] = spec
        if is_lazy:
            self._factories[spec.name] = implementation_or_factory
        else:
            self._impls[spec.name] = implementation_or_factory
            
        logger.info("specialist_registered", name=spec.name, version=spec.version, provider=spec.provider, lazy=is_lazy)

    def get_specialist(self, name: str) -> Specialist:
        """Return specialist implementation (instantiating if lazy loaded). Raises InvalidToolRequestError if not found."""
        if name not in self._specs:
            raise InvalidToolRequestError(
                message=f"Specialist '{name}' is not registered or is disabled."
            )
            
        # Check availability
        if self._specs[name].availability_status == "unavailable":
            raise NoSpecialistAvailableError(message=f"Specialist '{name}' is currently unavailable.")

        if name not in self._impls:
            # Lazy load
            try:
                self._specs[name].availability_status = "loading"
                factory = self._factories[name]
                self._impls[name] = factory()
                self._specs[name].availability_status = "available"
            except Exception as e:
                self._specs[name].availability_status = "unavailable"
                raise NoSpecialistAvailableError(message=f"Failed to load specialist '{name}': {e}")
                
        return self._impls[name]

    def unload_specialist(self, name: str) -> None:
        """Gracefully unload a specialist from memory if it was lazy loaded."""
        if name in self._factories and name in self._impls:
            del self._impls[name]
            logger.info("specialist_unloaded", name=name)

    def check_availability(self, name: str) -> str:
        """Return the availability status of the model."""
        spec = self._specs.get(name)
        return spec.availability_status if spec else "unregistered"

    def get_spec(self, name: str) -> ToolSpec:
        """Return ToolSpec. Raises InvalidToolRequestError if not found."""
        spec = self._specs.get(name)
        if not spec:
            raise InvalidToolRequestError(
                message=f"No ToolSpec registered for '{name}'."
            )
        return spec

    def list_tools(self) -> list[ToolSpec]:
        """Return all registered (enabled) tool specs."""
        return list(self._specs.values())

    def find_by_capability(self, capability: str) -> list[ToolSpec]:
        """Find all enabled tools that support a given capability."""
        return [
            spec for spec in self._specs.values()
            if capability in spec.capabilities
        ]

    def find_for_config_and_intent(
        self,
        input_configuration: str,
        intent: str,
        capabilities: list[str],
    ) -> ToolSpec | None:
        """
        Find the best registered tool for a given (config, intent, capabilities) combination.
        
        Priority: more specific capability match wins.
        """
        candidates: list[ToolSpec] = []

        for spec in self._specs.values():
            config_ok = (
                input_configuration in spec.supported_input_configurations
                or "ALL" in spec.supported_input_configurations
            )
            intent_ok = (
                intent in spec.supported_intents
                or "ALL" in spec.supported_intents
            )
            cap_ok = any(cap in spec.capabilities for cap in capabilities)

            if config_ok and intent_ok and cap_ok:
                candidates.append(spec)

        if not candidates:
            return None

        # Score by number of matching capabilities (more specific = better)
        def score(spec: ToolSpec) -> int:
            return sum(1 for cap in capabilities if cap in spec.capabilities)

        return max(candidates, key=score)

    def bootstrap(self) -> None:
        """Register all built-in specialists. Called at app startup."""
        from app.specialists.single_image import MockSingleImageSpecialist
        from app.specialists.optical_sar import MockOpticalSARSpecialist
        from app.specialists.change_detection import MockChangeDetectionSpecialist
        from app.specialists.grounding import MockGroundingSpecialist

        self.register(
            ToolSpec(
                name="mock_single_image",
                version="0.1.0",
                display_name="Mock Single Image Analyst",
                description="Mock specialist for single optical/SAR image analysis (VQA, scene description, object identification)",
                capabilities=[
                    Capability.SINGLE_IMAGE_ANALYSIS,
                    Capability.VQA,
                    Capability.SCENE_DESCRIPTION,
                    Capability.OBJECT_IDENTIFICATION,
                    Capability.BUILT_UP_ANALYSIS,
                    Capability.WATER_ANALYSIS,
                ],
                supported_input_configurations=["SINGLE_OPTICAL", "SINGLE_SAR"],
                supported_intents=[
                    "SCENE_DESCRIPTION", "VQA", "OBJECT_IDENTIFICATION",
                    "BUILT_UP_ANALYSIS", "WATER_ANALYSIS", "UNKNOWN",
                ],
                provider="mock",
                model_status="mock",
                timeout_seconds=30,
            ),
            MockSingleImageSpecialist,
            is_lazy=True,
        )

        self.register(
            ToolSpec(
                name="mock_optical_sar",
                version="0.1.0",
                display_name="Mock Optical+SAR Fusion Analyst",
                description="Mock specialist for optical + SAR pair analysis including built-up and water detection",
                capabilities=[
                    Capability.OPTICAL_SAR_FUSION,
                    Capability.BUILT_UP_ANALYSIS,
                    Capability.WATER_ANALYSIS,
                ],
                supported_input_configurations=["OPTICAL_SAR_PAIR"],
                supported_intents=[
                    "OPTICAL_SAR_ANALYSIS", "BUILT_UP_ANALYSIS", "WATER_ANALYSIS",
                    "SCENE_DESCRIPTION", "UNKNOWN",
                ],
                provider="mock",
                model_status="mock",
                timeout_seconds=45,
            ),
            MockOpticalSARSpecialist,
            is_lazy=True,
        )

        self.register(
            ToolSpec(
                name="mock_change_detection",
                version="0.1.0",
                display_name="Mock Change Detection Specialist",
                description="Mock specialist for bi-temporal change detection and analysis",
                capabilities=[
                    Capability.CHANGE_DETECTION,
                    Capability.CHANGE_VQA,
                ],
                supported_input_configurations=["BI_TEMPORAL"],
                supported_intents=[
                    "CHANGE_DESCRIPTION", "CHANGE_VQA", "BUILT_UP_ANALYSIS",
                    "WATER_ANALYSIS", "UNKNOWN",
                ],
                provider="mock",
                model_status="mock",
                timeout_seconds=45,
            ),
            MockChangeDetectionSpecialist,
            is_lazy=True,
        )

        self.register(
            ToolSpec(
                name="mock_grounding",
                version="0.1.0",
                display_name="Mock Grounding Specialist",
                description="Mock specialist for text-guided region grounding and localization",
                capabilities=[Capability.GROUNDING],
                supported_input_configurations=["SINGLE_OPTICAL", "SINGLE_SAR"],
                supported_intents=["GROUNDING"],
                provider="mock",
                model_status="mock",
                timeout_seconds=30,
            ),
            MockGroundingSpecialist,
            is_lazy=True,
        )
