"""
SatQuery AI — Query Intent Classifier (Planner)

Classifies user query into a structured intent.

Current implementation: keyword-based deterministic rules.
Architecture allows future replacement with LLM/function-calling
without changing the router or specialists.

Output always conforms to IntentResult schema.
"""

import re

from app.core.logging import get_logger
from app.models.schemas import InputConfiguration, IntentResult, QueryIntent

logger = get_logger(__name__)

# --- Keyword rule sets ---
# Each rule: (pattern_list, intent, base_confidence)
# Patterns are checked against lower-cased query.

INTENT_RULES: list[tuple[list[str], QueryIntent, float]] = [
    # Change detection — must come before general description to avoid false matches
    (["what changed", "change between", "changes between", "change detection",
      "has.*changed", "differ.*between", "difference between", "before.*after"],
     QueryIntent.CHANGE_DESCRIPTION, 0.88),

    (["how.*changed", "where.*changed", "changed.*built", "built.*increased",
      "new.*construction", "deforestation", "urban.*expansion", "change.*vqa"],
     QueryIntent.CHANGE_VQA, 0.85),

    # Grounding
    (["where is", "locate", "find", "point to", "bounding box", "ground", "region of",
      "mark", "highlight", "show me where"],
     QueryIntent.GROUNDING, 0.85),

    # Built-up / urban
    (["built.up", "urban", "building", "infrastructure", "settlement", "city",
      "town", "road", "highway"],
     QueryIntent.BUILT_UP_ANALYSIS, 0.82),

    # Water
    (["water", "flood", "lake", "river", "reservoir", "wetland", "ocean", "sea",
      "inundation", "water body"],
     QueryIntent.WATER_ANALYSIS, 0.82),

    # Optical+SAR
    (["sar", "radar", "synthetic aperture", "backscatter", "optical.*sar",
      "sar.*optical", "both images", "combine", "fusion"],
     QueryIntent.OPTICAL_SAR_ANALYSIS, 0.84),

    # VQA — specific questions
    (["how many", "count", "number of", "what is the", "what are the",
      "percentage", "area of", "proportion"],
     QueryIntent.VQA, 0.80),

    # Object identification
    (["identify", "detect", "object", "feature", "land cover", "class",
      "segment", "type of", "what kind"],
     QueryIntent.OBJECT_IDENTIFICATION, 0.78),

    # Scene description — broad/general (lowest priority)
    (["describe", "what.*see", "overview", "summary", "explain", "tell me about",
      "general", "show", "analyze"],
     QueryIntent.SCENE_DESCRIPTION, 0.72),
]

# Configuration-specific intent overrides
CONFIG_INTENT_MAP: dict[InputConfiguration, QueryIntent] = {
    InputConfiguration.BI_TEMPORAL: QueryIntent.CHANGE_DESCRIPTION,
    InputConfiguration.OPTICAL_SAR_PAIR: QueryIntent.OPTICAL_SAR_ANALYSIS,
}


def classify_intent(query: str, input_config: InputConfiguration) -> IntentResult:
    """
    Classify the user query into a structured intent.
    
    Priority:
    1. Rule-based keyword matching
    2. Configuration-context override for ambiguous cases
    3. Default fallback
    """
    query_lower = query.lower().strip()

    # Try keyword rules
    best_intent: QueryIntent | None = None
    best_confidence: float = 0.0
    required_capabilities: list[str] = []

    for patterns, intent, base_conf in INTENT_RULES:
        for pattern in patterns:
            if re.search(pattern, query_lower):
                if base_conf > best_confidence:
                    best_confidence = base_conf
                    best_intent = intent
                break  # Found a match for this rule, move to next rule

    # Apply configuration context — if config strongly suggests an intent, boost it
    if input_config in CONFIG_INTENT_MAP:
        config_intent = CONFIG_INTENT_MAP[input_config]
        if best_intent is None:
            # No keyword match — use configuration default
            best_intent = config_intent
            best_confidence = 0.70
        elif best_intent == QueryIntent.SCENE_DESCRIPTION and input_config == InputConfiguration.BI_TEMPORAL:
            # Generic query on bi-temporal config defaults to change detection
            best_intent = config_intent
            best_confidence = 0.75
        elif best_intent != config_intent:
            # Specific keyword matched different intent — let keyword win but reduce confidence slightly
            best_confidence = max(0.60, best_confidence - 0.08)

    # Final fallback
    if best_intent is None:
        best_intent = QueryIntent.SCENE_DESCRIPTION
        best_confidence = 0.55

    # Map intent to required capabilities
    required_capabilities = _get_required_capabilities(best_intent, input_config)

    result = IntentResult(
        type=best_intent,
        confidence=best_confidence,
        required_capabilities=required_capabilities,
    )

    logger.info(
        "intent_classified",
        intent=best_intent.value,
        confidence=best_confidence,
        config=input_config.value,
    )

    return result


def _get_required_capabilities(intent: QueryIntent, config: InputConfiguration) -> list[str]:
    """Map intent + config to required capability names."""
    base: list[str] = []

    if intent in (QueryIntent.SCENE_DESCRIPTION, QueryIntent.VQA, QueryIntent.OBJECT_IDENTIFICATION):
        base.append("single_image_analysis")

    if intent == QueryIntent.GROUNDING:
        base.append("grounding")

    if intent in (QueryIntent.CHANGE_DESCRIPTION, QueryIntent.CHANGE_VQA):
        base.append("change_detection")

    if intent in (QueryIntent.BUILT_UP_ANALYSIS, QueryIntent.WATER_ANALYSIS):
        if config == InputConfiguration.OPTICAL_SAR_PAIR:
            base.append("optical_sar_fusion")
        else:
            base.append("single_image_analysis")

    if intent == QueryIntent.OPTICAL_SAR_ANALYSIS or config == InputConfiguration.OPTICAL_SAR_PAIR:
        base.append("optical_sar_fusion")

    return list(dict.fromkeys(base))  # deduplicate while preserving order
