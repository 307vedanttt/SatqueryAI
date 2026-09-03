"""
Captioning operations using Qwen2.5-VL-3B-Instruct.
"""
import logging
from PIL import Image
from schemas.contracts import SpecialistRequest, SpecialistResponse
from models.vqa.model_loader import get_model_and_processor

logger = logging.getLogger(__name__)

def run_captioning(request: SpecialistRequest) -> SpecialistResponse:
    """
    Runs image captioning on exactly one image.
    Overrides the request query with a fixed captioning prompt.
    """
    if not request.images or len(request.images) != 1:
        return SpecialistResponse(
            task="captioning",
            answer="",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message="run_captioning requires exactly 1 image in the request."
        )
        
    try:
        model, processor = get_model_and_processor()
        from qwen_vl_utils import process_vision_info
        
        image = Image.open(request.images[0].file_path)
        
        fixed_query = "Describe the land cover and major objects visible in this image."
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": fixed_query},
                ],
            }
        ]
        
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        ).to(model.device)
        
        output_ids = model.generate(**inputs, max_new_tokens=256)
        
        # Trim generated tokens that were in input
        generated_ids = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, output_ids)
        ]
        
        decoded_text = processor.batch_decode(
            generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
        )[0]
        
        return SpecialistResponse(
            task="captioning",
            answer=decoded_text,
            confidence=0.9,
            confidence_tier="high",
            status="success",
            model_used="Qwen2.5-VL-3B-Instruct",
            evidence="Generated from full-image analysis, no region-specific grounding applied"
        )
        
    except Exception as e:
        logger.exception("Exception occurred during captioning execution")
        return SpecialistResponse(
            task="captioning",
            answer="",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=f"Exception during captioning generation: {str(e)}"
        )
