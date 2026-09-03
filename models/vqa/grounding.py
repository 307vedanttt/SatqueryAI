"""
SatQuery AI — Grounding Specialist (Person B)

Executes text-guided region grounding using Qwen2.5-VL bounding box outputs.

IMPORTANT LIMITATION NOTE:
  This module produces visual localization (bounding boxes within normalized/pixel image coordinates).
  It does NOT output real-world geographic coordinates (latitude/longitude).
"""

import logging
import re
from typing import Optional
from PIL import Image
from schemas.contracts import BoundingBox, SpecialistRequest, SpecialistResponse
from models.vqa.model_loader import get_model_and_processor

logger = logging.getLogger("satquery.models.vqa.grounding")


def parse_bbox_from_text(text: str, label: str = "target object") -> Optional[BoundingBox]:
    """
    Extract bounding box coordinates from text output.
    Looks for pattern like [ymin, xmin, ymax, xmax] or [xmin, ymin, xmax, ymax] (4 numbers).
    """
    # Matches [123, 456, 789, 900] or (123, 456, 789, 900)
    match = re.search(r"[\[\(]\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*[\]\)]", text)
    if not match:
        # Fallback: find any sequence of 4 numbers
        nums = re.findall(r"\b\d+\b", text)
        if len(nums) >= 4:
            val1, val2, val3, val4 = map(float, nums[:4])
            return BoundingBox(
                label=label,
                xmin=min(val1, val3),
                ymin=min(val2, val4),
                xmax=max(val1, val3),
                ymax=max(val2, val4),
            )
        return None

    val1, val2, val3, val4 = map(float, match.groups())
    return BoundingBox(
        label=label,
        xmin=min(val1, val3),
        ymin=min(val2, val4),
        xmax=max(val1, val3),
        ymax=max(val2, val4),
    )


def run_grounding(request: SpecialistRequest) -> SpecialistResponse:
    """Run region grounding and bounding box localization."""
    if len(request.images) != 1:
        return SpecialistResponse(
            task="grounding",
            answer="Error: Grounding requires exactly 1 image.",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=f"Grounding requires exactly 1 image, got {len(request.images)}",
        )

    file_path = request.images[0].file_path

    try:
        image = Image.open(file_path).convert("RGB")
    except Exception as e:
        return SpecialistResponse(
            task="grounding",
            answer=f"Error loading image: {e}",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=str(e),
        )

    try:
        model, processor = get_model_and_processor()

        ground_prompt = (
            f"Identify and locate '{request.query}' in the image. "
            "Return the bounding box coordinates in format [ymin, xmin, ymax, xmax] normalized 0-1000."
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": ground_prompt},
                ],
            }
        ]

        text_prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[text_prompt], images=[image], padding=True, return_tensors="pt")

        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        output_ids = model.generate(**inputs, max_new_tokens=256)
        generated_ids = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs["input_ids"], output_ids)]
        output_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

        bbox = parse_bbox_from_text(output_text, label=request.query)

        if bbox is None:
            logger.warning(f"Failed to parse bounding box from model output: '{output_text}'")
            return SpecialistResponse(
                task="grounding",
                answer=f"Grounding failed: Coordinate parsing failed from model response '{output_text[:100]}...'",
                confidence=0.0,
                confidence_tier="insufficient",
                status="error",
                error_message="Coordinate parsing failed from model output.",
            )

        return SpecialistResponse(
            task="grounding",
            answer=f"Grounded region for '{request.query}': Bounding box [{bbox.xmin:.0f}, {bbox.ymin:.0f}, {bbox.xmax:.0f}, {bbox.ymax:.0f}]",
            confidence=0.82,
            confidence_tier="high",
            bounding_boxes=[bbox],
            evidence=["Visual localization within normalized image space (0-1000)"],
            model_used="Qwen2.5-VL-3B-Instruct",
            status="success",
        )

    except Exception as e:
        logger.error(f"Grounding exception: {e}")
        return SpecialistResponse(
            task="grounding",
            answer=f"Grounding error: {e}",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=str(e),
        )
