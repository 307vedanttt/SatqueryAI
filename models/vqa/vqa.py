"""
SatQuery AI — Single Image VQA Specialist (Person B)

Executes visual question answering using Qwen2.5-VL-3B-Instruct.
Note: Qwen2.5-VL is a general-purpose vision-language model, not remote-sensing specialized.
"""

import logging
from PIL import Image
from schemas.contracts import SpecialistRequest, SpecialistResponse
from models.vqa.model_loader import get_model_and_processor

logger = logging.getLogger("satquery.models.vqa.vqa")


def run_vqa(request: SpecialistRequest) -> SpecialistResponse:
    """Run VQA on a single image."""
    if len(request.images) != 1:
        return SpecialistResponse(
            task="vqa",
            answer="Error: VQA requires exactly 1 image.",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=f"VQA requires exactly 1 image, got {len(request.images)}",
        )

    image_info = request.images[0]
    file_path = image_info.file_path

    try:
        image = Image.open(file_path).convert("RGB")
    except Exception as e:
        logger.error(f"Failed to open image file '{file_path}': {e}")
        return SpecialistResponse(
            task="vqa",
            answer=f"Error loading image: {e}",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=str(e),
        )

    try:
        model, processor = get_model_and_processor()

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": request.query},
                ],
            }
        ]

        text_prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[text_prompt], images=[image], padding=True, return_tensors="pt")

        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        output_ids = model.generate(**inputs, max_new_tokens=256)
        generated_ids = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs["input_ids"], output_ids)
        ]
        output_text = processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)[0]

        return SpecialistResponse(
            task="vqa",
            answer=output_text.strip(),
            confidence=0.85,
            confidence_tier="high",
            bounding_boxes=[],
            evidence=["Generated from full-image analysis, no region-specific grounding applied"],
            model_used="Qwen2.5-VL-3B-Instruct",
            status="success",
        )

    except Exception as e:
        logger.error(f"VQA generation exception: {e}")
        return SpecialistResponse(
            task="vqa",
            answer=f"Model generation error: {e}",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=str(e),
        )
