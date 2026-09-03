"""
SatQuery AI — Bounded Execution Graph

Maps (InputConfiguration, IntentResult) to an ordered execution plan.
The router can ONLY select tools from the registered registry.
No arbitrary tool calls are possible.

This is a deterministic state machine, not a free-form agent.
"""

from app.core.exceptions import NoSpecialistAvailableError
from app.core.logging import get_logger
from app.models.schemas import InputConfiguration, IntentResult, QueryIntent, RoutePlan
from app.registry.registry import SpecialistRegistry

logger = get_logger(__name__)

# ---- Routing table -------------------------------------------------------
# Maps (InputConfiguration, QueryIntent) to specialist name.
# 'DEFAULT' is used when no specific match exists for the intent.
# This table is the ONLY place routing decisions are made.

ROUTING_TABLE: dict[tuple[str, str], str] = {
    # Single Optical
    ("SINGLE_OPTICAL", "SCENE_DESCRIPTION"):     "mock_single_image",
    ("SINGLE_OPTICAL", "VQA"):                   "mock_single_image",
    ("SINGLE_OPTICAL", "OBJECT_IDENTIFICATION"): "mock_single_image",
    ("SINGLE_OPTICAL", "BUILT_UP_ANALYSIS"):     "mock_single_image",
    ("SINGLE_OPTICAL", "WATER_ANALYSIS"):        "mock_single_image",
    ("SINGLE_OPTICAL", "GROUNDING"):             "mock_grounding",
    ("SINGLE_OPTICAL", "UNKNOWN"):               "mock_single_image",

    # Single SAR
    ("SINGLE_SAR", "SCENE_DESCRIPTION"):         "mock_single_image",
    ("SINGLE_SAR", "VQA"):                       "mock_single_image",
    ("SINGLE_SAR", "OBJECT_IDENTIFICATION"):     "mock_single_image",
    ("SINGLE_SAR", "BUILT_UP_ANALYSIS"):         "mock_single_image",
    ("SINGLE_SAR", "WATER_ANALYSIS"):            "mock_single_image",
    ("SINGLE_SAR", "UNKNOWN"):                   "mock_single_image",

    # Optical + SAR Pair
    ("OPTICAL_SAR_PAIR", "OPTICAL_SAR_ANALYSIS"): "mock_optical_sar",
    ("OPTICAL_SAR_PAIR", "BUILT_UP_ANALYSIS"):    "mock_optical_sar",
    ("OPTICAL_SAR_PAIR", "WATER_ANALYSIS"):       "mock_optical_sar",
    ("OPTICAL_SAR_PAIR", "SCENE_DESCRIPTION"):    "mock_optical_sar",
    ("OPTICAL_SAR_PAIR", "VQA"):                  "mock_optical_sar",
    ("OPTICAL_SAR_PAIR", "UNKNOWN"):              "mock_optical_sar",

    # Bi-temporal
    ("BI_TEMPORAL", "CHANGE_DESCRIPTION"):       "mock_change_detection",
    ("BI_TEMPORAL", "CHANGE_VQA"):               "mock_change_detection",
    ("BI_TEMPORAL", "BUILT_UP_ANALYSIS"):        "mock_change_detection",
    ("BI_TEMPORAL", "WATER_ANALYSIS"):           "mock_change_detection",
    ("BI_TEMPORAL", "SCENE_DESCRIPTION"):        "mock_change_detection",
    ("BI_TEMPORAL", "VQA"):                      "mock_change_detection",
    ("BI_TEMPORAL", "UNKNOWN"):                  "mock_change_detection",
}

# Fixed execution steps for each specialist (ordered pipeline)
SPECIALIST_STEPS: dict[str, list[str]] = {
    "mock_single_image": [
        "validate_input",
        "preprocess_image",
        "run_vision_analysis",
        "extract_evidence",
        "synthesize_response",
    ],
    "mock_optical_sar": [
        "validate_pair",
        "run_optical_analysis",
        "run_sar_analysis",
        "fuse_results",
        "detect_disagreement",
        "extract_evidence",
        "synthesize_response",
    ],
    "mock_change_detection": [
        "validate_temporal_pair",
        "compute_difference",
        "classify_changes",
        "extract_change_evidence",
        "synthesize_response",
    ],
    "mock_grounding": [
        "validate_input",
        "parse_grounding_query",
        "localize_regions",
        "extract_bbox_evidence",
        "synthesize_response",
    ],
}


class ExecutionGraph:
    """
    Bounded execution graph — maps routing inputs to an ordered
    list of execution steps and a selected specialist.
    
    Cannot call arbitrary tools. Only registered specialists in ROUTING_TABLE.
    """

    def __init__(self, registry: SpecialistRegistry) -> None:
        self.registry = registry

    def plan(self, input_config: InputConfiguration, intent: IntentResult) -> RoutePlan:
        """
        Build an execution plan for the given input configuration and intent.
        
        Strategy:
        1. Try exact (config, intent) lookup in ROUTING_TABLE
        2. Fall back to registry capability-based lookup
        3. Raise NoSpecialistAvailableError if no match found
        """
        config_str = input_config.value
        intent_str = intent.type.value

        # 1. Exact routing table lookup
        specialist_name = ROUTING_TABLE.get((config_str, intent_str))

        # 2. Fallback: try UNKNOWN intent for this config
        if not specialist_name:
            specialist_name = ROUTING_TABLE.get((config_str, "UNKNOWN"))

        # 3. Fallback: capability-based registry lookup
        if not specialist_name:
            spec = self.registry.find_for_config_and_intent(
                config_str, intent_str, intent.required_capabilities
            )
            if spec:
                specialist_name = spec.name

        if not specialist_name:
            logger.warning(
                "no_specialist_found",
                config=config_str,
                intent=intent_str,
            )
            raise NoSpecialistAvailableError(
                message=(
                    f"No specialist available for configuration '{config_str}' "
                    f"and intent '{intent_str}'."
                )
            )

        # Verify the selected specialist is actually registered
        self.registry.get_spec(specialist_name)  # raises if not registered

        steps = SPECIALIST_STEPS.get(specialist_name, ["execute"])

        logger.info(
            "route_planned",
            specialist=specialist_name,
            config=config_str,
            intent=intent_str,
            steps=steps,
        )

        return RoutePlan(
            input_configuration=input_config,
            intent=intent,
            execution_steps=steps,
            specialist=specialist_name,
        )
