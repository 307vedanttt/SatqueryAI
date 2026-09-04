from pydantic import BaseModel
from typing import Any
from app.models.schemas import InputConfiguration, ImageMetadata
from app.registry.registry import SpecialistRegistry
from app.router.classifier import classify_input_configuration
from app.router.planner import classify_intent
from app.router.execution_graph import ExecutionGraph
from app.core.exceptions import NoSpecialistAvailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

class RouterResult(BaseModel):
    configuration: str
    intent: str
    selected_specialist: str | None
    reason: str
    execution_plan: list[str]
    confidence: float

class BoundedQueryRouter:
    """
    Deterministic router that maps validated inputs to an execution graph
    using fixed boundaries and strict input validation.
    """
    def __init__(self, registry: SpecialistRegistry):
        self.registry = registry
        self.execution_graph = ExecutionGraph(registry)

    def route(
        self,
        query: str,
        metadata: list[ImageMetadata]
    ) -> RouterResult:
        
        # 1. Input Validation
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
            
        if not metadata:
            raise ValueError("At least one image metadata record is required.")

        # 2. Detect Configuration
        input_config = classify_input_configuration(metadata)
        if input_config == InputConfiguration.UNKNOWN:
            raise ValueError("Invalid or unsupported image configuration.")

        # 3. Detect Intent
        intent_result = classify_intent(query, input_config)
        
        if intent_result.type.value == "UNKNOWN":
            raise ValueError("Unsupported query intent. Cannot determine the required task.")

        # 4. Select Specialist (using execution graph planner)
        try:
            route_plan = self.execution_graph.plan(input_config, intent_result)
        except NoSpecialistAvailableError as e:
            # Re-raise with strict failure rule
            raise RuntimeError(f"Required model unavailable: {e.message}") from e

        # 5. Model Availability Check
        status = self.registry.check_availability(route_plan.specialist)
        if status == "unavailable":
            raise RuntimeError(f"Specialist '{route_plan.specialist}' is currently unavailable.")

        # Create audit trail
        reason = (
            f"Config '{input_config.value}' and Intent '{intent_result.type.value}' "
            f"mapped to '{route_plan.specialist}' with confidence {intent_result.confidence:.2f}."
        )

        return RouterResult(
            configuration=input_config.value,
            intent=intent_result.type.value,
            selected_specialist=route_plan.specialist,
            reason=reason,
            execution_plan=route_plan.execution_steps,
            confidence=intent_result.confidence
        )
