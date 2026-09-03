"""
SatQuery AI — Capability Constants

Defines the set of capability strings used throughout the system.
The router maps intents to these capabilities.
The registry maps capabilities to registered tools.
"""


class Capability:
    """Namespace for capability string constants."""

    SINGLE_IMAGE_ANALYSIS = "single_image_analysis"
    VQA = "vqa"
    SCENE_DESCRIPTION = "scene_description"
    GROUNDING = "grounding"
    CHANGE_DETECTION = "change_detection"
    CHANGE_VQA = "change_vqa"
    OPTICAL_SAR_FUSION = "optical_sar_fusion"
    BUILT_UP_ANALYSIS = "built_up_analysis"
    WATER_ANALYSIS = "water_analysis"
    OBJECT_IDENTIFICATION = "object_identification"

    # All defined capabilities
    ALL: list[str] = [
        SINGLE_IMAGE_ANALYSIS,
        VQA,
        SCENE_DESCRIPTION,
        GROUNDING,
        CHANGE_DETECTION,
        CHANGE_VQA,
        OPTICAL_SAR_FUSION,
        BUILT_UP_ANALYSIS,
        WATER_ANALYSIS,
        OBJECT_IDENTIFICATION,
    ]
