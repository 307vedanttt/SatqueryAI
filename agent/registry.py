"""
SatQuery AI — Agent Tool Registry (Person A)

Holds a fixed dictionary of six tools:
  - single_image_vqa
  - caption_image
  - ground_region
  - change_detection
  - change_vqa
  - optical_sar_fusion

Each tool has precondition checking logic and dynamic stub/real callable swapping.
"""

from typing import Callable, Tuple
from schemas.contracts import SpecialistRequest, SpecialistResponse


def _stub_specialist(task_name: str) -> Callable[[SpecialistRequest], SpecialistResponse]:
    def stub(request: SpecialistRequest) -> SpecialistResponse:
        return SpecialistResponse(
            task=task_name,
            answer=f"[STUB - awaiting real model integration] Response for task '{task_name}' on query: '{request.query}'",
            confidence=0.75,
            confidence_tier="moderate",
            bounding_boxes=[],
            evidence=[f"Stub execution for {task_name}"],
            model_used=f"STUB-{task_name}",
            status="success",
            error_message=None,
        )
    return stub


# ---- Precondition Check Functions ---------------------------------------

def check_single_image(request: SpecialistRequest) -> Tuple[bool, str]:
    if len(request.images) != 1:
        return False, f"Requires exactly 1 image, got {len(request.images)}"
    return True, "Precondition passed: exactly 1 image provided"


def check_change_detection(request: SpecialistRequest) -> Tuple[bool, str]:
    if len(request.images) != 2:
        return False, f"Requires exactly 2 images, got {len(request.images)}"

    img1, img2 = request.images[0], request.images[1]

    # Check same sensor
    s1, s2 = (img1.sensor or "").lower(), (img2.sensor or "").lower()
    if s1 != s2:
        return False, f"Sensor mismatch for change detection: '{s1}' vs '{s2}'"

    # Check CRS matching if present
    c1, c2 = (img1.crs or "").upper(), (img2.crs or "").upper()
    if c1 != "NONE" and c2 != "NONE" and c1 != c2:
        return False, f"CRS mismatch for change detection: '{c1}' vs '{c2}'"

    # Check resolution within 10%
    r1, r2 = img1.resolution_m, img2.resolution_m
    if r1 > 0 and r2 > 0:
        diff = abs(r1 - r2) / max(r1, r2)
        if diff > 0.10:
            return False, f"Resolution mismatch exceeds 10% tolerance: {r1}m vs {r2}m ({diff*100:.1f}% diff)"

    return True, "Precondition passed: 2 images, same sensor, matching CRS and resolution"


def check_optical_sar_fusion(request: SpecialistRequest) -> Tuple[bool, str]:
    if len(request.images) != 2:
        return False, f"Requires exactly 2 images, got {len(request.images)}"

    sensors = {(img.sensor or "").lower() for img in request.images}
    if not ("optical" in sensors and "sar" in sensors):
        return False, f"Requires 1 optical and 1 SAR image, got sensors: {list(sensors)}"

    img1, img2 = request.images[0], request.images[1]
    c1, c2 = (img1.crs or "").upper(), (img2.crs or "").upper()
    if c1 != "NONE" and c2 != "NONE" and c1 != c2:
        return False, f"CRS mismatch for Optical-SAR fusion: '{c1}' vs '{c2}'"

    return True, "Precondition passed: 1 optical + 1 SAR image with matching CRS"


class ToolEntry:
    def __init__(
        self,
        name: str,
        callable_fn: Callable[[SpecialistRequest], SpecialistResponse],
        description: str,
        required_inputs: list[str],
        precondition_fn: Callable[[SpecialistRequest], Tuple[bool, str]],
    ):
        self.name = name
        self.callable_fn = callable_fn
        self.description = description
        self.required_inputs = required_inputs
        self.precondition_fn = precondition_fn


class ToolRegistry:
    """Central ToolRegistry containing fixed dictionary of 6 tools."""

    def __init__(self):
        self._tools: dict[str, ToolEntry] = {}
        self._bootstrap_stubs()

    def _bootstrap_stubs(self):
        """Register initial stub implementations for all six tools."""
        self.register_tool(
            name="single_image_vqa",
            callable_fn=_stub_specialist("single_image_vqa"),
            precondition_fn=check_single_image,
            description="Single image visual question answering",
            required_inputs=["1 optical or SAR image"],
        )

        self.register_tool(
            name="caption_image",
            callable_fn=_stub_specialist("caption_image"),
            precondition_fn=check_single_image,
            description="Single image scene description and captioning",
            required_inputs=["1 optical or SAR image"],
        )

        self.register_tool(
            name="ground_region",
            callable_fn=_stub_specialist("ground_region"),
            precondition_fn=check_single_image,
            description="Text-guided region grounding and object localization",
            required_inputs=["1 optical or SAR image"],
        )

        self.register_tool(
            name="change_detection",
            callable_fn=_stub_specialist("change_detection"),
            precondition_fn=check_change_detection,
            description="Bi-temporal change detection analysis",
            required_inputs=["2 images, same sensor, matching CRS and resolution"],
        )

        self.register_tool(
            name="change_vqa",
            callable_fn=_stub_specialist("change_vqa"),
            precondition_fn=check_change_detection,
            description="Bi-temporal change question answering",
            required_inputs=["2 images, same sensor, matching CRS and resolution"],
        )

        self.register_tool(
            name="optical_sar_fusion",
            callable_fn=_stub_specialist("optical_sar_fusion"),
            precondition_fn=check_optical_sar_fusion,
            description="Optical + SAR multimodal image fusion",
            required_inputs=["2 images: 1 optical + 1 SAR, matching CRS"],
        )

    def register_tool(
        self,
        name: str,
        callable_fn: Callable[[SpecialistRequest], SpecialistResponse],
        precondition_fn: Callable[[SpecialistRequest], Tuple[bool, str]],
        description: str = "",
        required_inputs: list[str] = None,
    ):
        """Register or swap a tool callable and precondition function."""
        entry = ToolEntry(
            name=name,
            callable_fn=callable_fn,
            description=description or f"Tool: {name}",
            required_inputs=required_inputs or [],
            precondition_fn=precondition_fn,
        )
        self._tools[name] = entry

    def get_tool(self, name: str) -> ToolEntry:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in ToolRegistry.")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())
