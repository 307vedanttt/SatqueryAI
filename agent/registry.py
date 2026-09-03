"""
agent/registry.py — Tool Registry for SatQuery AI

The ToolRegistry is the SINGLE AUTHORISED list of tools the system may call.
No tool can be invoked by the executor unless it is registered here.
This design constraint directly prevents the "tool-selection from an open-ended
pool" failure mode documented in agentic system research.

All six tools are registered at module load time with:
  - A stub callable that returns a valid SpecialistResponse
  - A precondition-check function that validates the request BEFORE execution
  - Human-readable metadata for logging and tracing

STUB POLICY
-----------
Every callable registered here is initially a stub that returns:
    status="success", confidence_tier="moderate",
    answer="[STUB - awaiting real model integration]"

This lets agent/executor.py and all tests run completely end-to-end
without waiting for Persons B/C/D to finish their real model modules.

SWAPPING STUBS FOR REAL IMPLEMENTATIONS
----------------------------------------
Once a real model module is ready (e.g. models/vqa/vqa.py), replace the stub
with one call to register_tool():

    from models.vqa.vqa import run_vqa
    registry.register_tool(
        name="single_image_vqa",
        callable_fn=run_vqa,
        precondition_fn=registry._tools["single_image_vqa"]["precondition"],
    )

This requires NO changes to router.py or executor.py.
"""

import logging
from typing import Any, Callable, Optional

from schemas.contracts import ImageMetadata, SpecialistRequest, SpecialistResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Precondition helpers — shared logic used by multiple tools
# ---------------------------------------------------------------------------

def _resolution_within_10pct(meta1: ImageMetadata, meta2: ImageMetadata) -> bool:
    """
    Return True if both images have non-zero resolution and their
    resolutions agree within a 10 % relative tolerance.

    Zero-resolution images (benchmark PNGs with no geospatial metadata)
    pass this check vacuously — the calling precondition must decide
    whether zero-resolution images are acceptable for its use case.
    """
    r1 = meta1.resolution_m
    r2 = meta2.resolution_m
    if r1 == 0.0 or r2 == 0.0:
        # No geospatial resolution available — skip check
        return True
    rel_diff = abs(r1 - r2) / max(r1, r2)
    return rel_diff <= 0.10


# ---------------------------------------------------------------------------
# Stub callables — one per tool
# ---------------------------------------------------------------------------

def _stub_single_image_vqa(request: SpecialistRequest) -> SpecialistResponse:
    """Stub for single_image_vqa. Returns placeholder answer."""
    logger.debug("stub_single_image_vqa called for query=%r", request.query[:60])
    return SpecialistResponse(
        task="vqa",
        answer="[STUB - awaiting real model integration] Single-image VQA placeholder response.",
        confidence=0.5,
        confidence_tier="moderate",
        bounding_boxes=[],
        evidence="Stub callable — no real inference performed.",
        model_used="stub",
        status="success",
        error_message=None,
    )


def _stub_caption_image(request: SpecialistRequest) -> SpecialistResponse:
    """Stub for caption_image. Returns placeholder captioning answer."""
    logger.debug("stub_caption_image called")
    return SpecialistResponse(
        task="captioning",
        answer="[STUB - awaiting real model integration] Image captioning placeholder.",
        confidence=0.5,
        confidence_tier="moderate",
        bounding_boxes=[],
        evidence="Stub callable — no real inference performed.",
        model_used="stub",
        status="success",
        error_message=None,
    )


def _stub_ground_region(request: SpecialistRequest) -> SpecialistResponse:
    """Stub for ground_region. Returns placeholder grounding answer."""
    logger.debug("stub_ground_region called")
    return SpecialistResponse(
        task="grounding",
        answer="[STUB - awaiting real model integration] Region grounding placeholder.",
        confidence=0.5,
        confidence_tier="moderate",
        bounding_boxes=[],
        evidence="Stub callable — no real inference performed.",
        model_used="stub",
        status="success",
        error_message=None,
    )


def _stub_change_detection(request: SpecialistRequest) -> SpecialistResponse:
    """Stub for change_detection. Returns placeholder change analysis answer."""
    logger.debug("stub_change_detection called")
    return SpecialistResponse(
        task="change_detection",
        answer="[STUB - awaiting real model integration] Change detection placeholder.",
        confidence=0.5,
        confidence_tier="moderate",
        bounding_boxes=[],
        evidence="Stub callable — no real inference performed.",
        model_used="stub",
        status="success",
        error_message=None,
    )


def _stub_change_vqa(request: SpecialistRequest) -> SpecialistResponse:
    """Stub for change_vqa. Returns placeholder change-VQA answer."""
    logger.debug("stub_change_vqa called")
    return SpecialistResponse(
        task="change_vqa",
        answer="[STUB - awaiting real model integration] Change VQA placeholder.",
        confidence=0.5,
        confidence_tier="moderate",
        bounding_boxes=[],
        evidence="Stub callable — no real inference performed.",
        model_used="stub",
        status="success",
        error_message=None,
    )


def _stub_optical_sar_fusion(request: SpecialistRequest) -> SpecialistResponse:
    """Stub for optical_sar_fusion. Returns placeholder fusion answer."""
    logger.debug("stub_optical_sar_fusion called")
    return SpecialistResponse(
        task="optical_sar_fusion",
        answer="[STUB - awaiting real model integration] Optical-SAR fusion placeholder.",
        confidence=0.5,
        confidence_tier="moderate",
        bounding_boxes=[],
        evidence="Stub callable — no real inference performed.",
        model_used="stub",
        status="success",
        error_message=None,
    )


# ---------------------------------------------------------------------------
# Precondition functions — one per tool
# ---------------------------------------------------------------------------

def _check_single_image(request: SpecialistRequest) -> tuple[bool, str]:
    """
    Precondition for single_image_vqa, caption_image, ground_region.
    Requires exactly 1 image. Returns (is_valid, reason_if_invalid).
    """
    n = len(request.images)
    if n != 1:
        return False, f"Tool requires exactly 1 image, but {n} were provided."
    return True, ""


def _crs_is_known(crs: str | None) -> bool:
    """Return True if crs is a real CRS string (not the 'none' sentinel or Python None)."""
    if crs is None:
        return False
    return crs.strip().lower() != "none"


def _check_change_pair(request: SpecialistRequest) -> tuple[bool, str]:
    """
    Precondition for change_detection and change_vqa.

    Requires:
      - Exactly 2 images
      - Both images have the same sensor type
      - If both have a real CRS (not 'none'), the CRS strings must match
      - If both have non-zero resolution, resolutions within 10 %

    These checks mirror what a human analyst would require before
    bi-temporal change detection is meaningful.
    """
    n = len(request.images)
    if n != 2:
        return False, f"Change detection requires exactly 2 images, but {n} were provided."

    img1, img2 = request.images[0], request.images[1]

    # Same sensor type
    if img1.sensor != img2.sensor:
        return False, (
            f"Change detection requires both images to have the same sensor type. "
            f"Got '{img1.sensor}' and '{img2.sensor}'."
        )

    # CRS must match (if both are known, i.e. not 'none' sentinel)
    if _crs_is_known(img1.crs) and _crs_is_known(img2.crs):
        if img1.crs.strip().upper() != img2.crs.strip().upper():
            return False, (
                f"CRS mismatch: image 1 has '{img1.crs}', image 2 has '{img2.crs}'. "
                "Reproject one image before change detection."
            )

    # Resolution must match within 10 % (if both are known)
    if not _resolution_within_10pct(img1, img2):
        return False, (
            f"Resolution mismatch: {img1.resolution_m:.1f} m vs {img2.resolution_m:.1f} m "
            "(>10% relative difference). Resample before change detection."
        )

    return True, ""


def _check_optical_sar(request: SpecialistRequest) -> tuple[bool, str]:
    """
    Precondition for optical_sar_fusion.

    Requires:
      - Exactly 2 images
      - One with sensor='optical' and one with sensor='sar'
      - If both have a real CRS (not 'none'), the CRS strings must match

    The optical and SAR images must be co-registered (same CRS) for
    pixel-level fusion to be physically meaningful.
    """
    n = len(request.images)
    if n != 2:
        return False, f"Optical-SAR fusion requires exactly 2 images, but {n} were provided."

    sensors = {img.sensor for img in request.images}
    if not ({"optical", "sar"} <= sensors):
        return False, (
            f"Optical-SAR fusion requires one 'optical' and one 'sar' image. "
            f"Got sensors: {sorted(sensors)}."
        )

    img1, img2 = request.images[0], request.images[1]
    if _crs_is_known(img1.crs) and _crs_is_known(img2.crs):
        if img1.crs.strip().upper() != img2.crs.strip().upper():
            return False, (
                f"CRS mismatch: '{img1.crs}' vs '{img2.crs}'. "
                "Optical and SAR images must share a CRS for fusion."
            )

    return True, ""


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """
    Central, bounded registry of all tools the agent is allowed to call.

    DESIGN PRINCIPLE (Bounded Execution)
    -------------------------------------
    The executor can ONLY invoke tools that exist in this registry.
    This prevents open-ended tool selection and is the primary mitigation
    against "fragile tool orchestration" failure modes in agentic systems.

    STRUCTURE OF EACH REGISTRY ENTRY
    ---------------------------------
    Each entry in _tools is a dict with four keys:
        "callable"     : Callable[[SpecialistRequest], SpecialistResponse]
        "description"  : str   — human-readable summary for logging
        "conditions"   : list[str] — plain-English preconditions
        "precondition" : Callable[[SpecialistRequest], tuple[bool, str]]
                         — check(request) -> (is_valid, reason_if_invalid)

    SWAPPING STUBS (post-hackathon)
    --------------------------------
    Use register_tool() to replace a stub callable with a real implementation.
    The precondition function is kept from the original registration.
    """

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}
        self._bootstrap()

    def _bootstrap(self) -> None:
        """
        Register all six tools with their stub callables and preconditions.
        Called once at construction time.
        """
        entries: list[tuple[str, Any, str, list[str], Any]] = [
            (
                "single_image_vqa",
                _stub_single_image_vqa,
                "Answer a specific question about a single satellite/aerial image "
                "using a vision-language model.",
                ["Exactly 1 image required"],
                _check_single_image,
            ),
            (
                "caption_image",
                _stub_caption_image,
                "Generate a structured scene description / caption for a single image, "
                "covering land cover and major visible objects.",
                ["Exactly 1 image required"],
                _check_single_image,
            ),
            (
                "ground_region",
                _stub_ground_region,
                "Locate and return a bounding box for a named region or object "
                "within a single image (visual grounding, NOT geographic coordinates).",
                ["Exactly 1 image required"],
                _check_single_image,
            ),
            (
                "change_detection",
                _stub_change_detection,
                "Detect and describe changes between two images of the same location "
                "taken at different times using a Siamese encoder architecture.",
                [
                    "Exactly 2 images required",
                    "Both images must have the same sensor type",
                    "CRS must match (if available)",
                    "Resolution must be within 10% (if available)",
                ],
                _check_change_pair,
            ),
            (
                "change_vqa",
                _stub_change_vqa,
                "Answer a specific question about changes detected between two bi-temporal "
                "images of the same location.",
                [
                    "Exactly 2 images required",
                    "Both images must have the same sensor type",
                    "CRS must match (if available)",
                    "Resolution must be within 10% (if available)",
                ],
                _check_change_pair,
            ),
            (
                "optical_sar_fusion",
                _stub_optical_sar_fusion,
                "Fuse an optical and SAR image pair using cross-attention fusion "
                "to answer a question leveraging complementary modalities.",
                [
                    "Exactly 2 images required",
                    "One image must be sensor='optical', the other sensor='sar'",
                    "CRS must match (if available)",
                ],
                _check_optical_sar,
            ),
        ]

        for name, callable_fn, description, conditions, precondition_fn in entries:
            self._tools[name] = {
                "callable": callable_fn,
                "description": description,
                "conditions": conditions,
                "precondition": precondition_fn,
            }
            logger.info("Tool registered: %s", name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_tool(
        self,
        name: str,
        callable_fn: Callable[[SpecialistRequest], SpecialistResponse],
        precondition_fn: Callable[[SpecialistRequest], tuple[bool, str]],
    ) -> None:
        """
        Register or replace a tool's callable and precondition.

        Use this to swap a stub for a real implementation without touching
        router.py or executor.py.

        Example (post-hackathon swap):
            from models.vqa.vqa import run_vqa
            registry.register_tool(
                name="single_image_vqa",
                callable_fn=run_vqa,
                precondition_fn=registry._tools["single_image_vqa"]["precondition"],
            )

        Args:
            name: Must be one of the six registered tool names.
            callable_fn: Function accepting SpecialistRequest, returning SpecialistResponse.
            precondition_fn: Function accepting SpecialistRequest, returning (bool, str).

        Raises:
            KeyError: If name is not a registered tool name.
        """
        if name not in self._tools:
            raise KeyError(
                f"Cannot register unknown tool '{name}'. "
                f"Known tools: {sorted(self._tools.keys())}"
            )
        self._tools[name]["callable"] = callable_fn
        self._tools[name]["precondition"] = precondition_fn
        logger.info("Tool updated (stub replaced with real implementation): %s", name)

    def get_callable(self, name: str) -> Callable[[SpecialistRequest], SpecialistResponse]:
        """
        Return the callable for the named tool.

        Args:
            name: Tool name.

        Raises:
            KeyError: If name is not registered.
        """
        if name not in self._tools:
            raise KeyError(
                f"Tool '{name}' not registered. "
                f"Known tools: {sorted(self._tools.keys())}"
            )
        return self._tools[name]["callable"]

    def check_precondition(
        self, name: str, request: SpecialistRequest
    ) -> tuple[bool, str]:
        """
        Run the precondition check for the named tool.

        Args:
            name: Tool name.
            request: The SpecialistRequest to validate.

        Returns:
            (True, "") if precondition passes.
            (False, reason) if precondition fails — reason explains why.

        Raises:
            KeyError: If name is not registered.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered.")
        return self._tools[name]["precondition"](request)

    def list_tools(self) -> list[str]:
        """Return sorted list of all registered tool names."""
        return sorted(self._tools.keys())

    def get_description(self, name: str) -> str:
        """Return the human-readable description for the named tool."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered.")
        return self._tools[name]["description"]

    def get_conditions(self, name: str) -> list[str]:
        """Return the list of plain-English precondition strings for the named tool."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered.")
        return self._tools[name]["conditions"]
