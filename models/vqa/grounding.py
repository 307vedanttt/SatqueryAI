"""
Grounding operations using Qwen2.5-VL-3B-Instruct.
"""
import re
import logging
from typing import Optional
from PIL import Image
from schemas.contracts import SpecialistRequest, SpecialistResponse, BoundingBox
from models.vqa.model_loader import get_model_and_processor

logger = logging.getLogger(__name__)


def parse_bbox_from_text(text: str) -> Optional[BoundingBox]:
    """
    Parses exactly 4 coordinate numbers from a string to form a BoundingBox.
    Handles formats like [123, 456, 789, 012] or <box>x1,y1,x2,y2</box>.
    """
    nums = re.findall(r'[-+]?\d*\.\d+|\d+', text)
    if len(nums) == 4:
        return BoundingBox(
            x1=float(nums[0]),
            y1=float(nums[1]),
            x2=float(nums[2]),
            y2=float(nums[3]),
            label="detected region",
            confidence=1.0
        )
    return None


def run_grounding(request: SpecialistRequest) -> SpecialistResponse:
    """
    Runs visual grounding on exactly one image.
    This produces visual localization within the image (pixel coordinates), NOT geographic coordinates (lat/lon). 
    Do not conflate image-space bounding boxes with real-world geographic extents.
    """
    if not request.images or len(request.images) != 1:
        return SpecialistResponse(
            task="grounding",
            answer="",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message="run_grounding requires exactly 1 image in the request."
        )
        
    try:
        model, processor = get_model_and_processor()
        from qwen_vl_utils import process_vision_info
        
        image = Image.open(request.images[0].file_path)
        
        prompt = f"Locate {request.query} in this image and return its bounding box coordinates as [x1, y1, x2, y2]."
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
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
        
        box = parse_bbox_from_text(decoded_text)
        
        if box:
            return SpecialistResponse(
                task="grounding",
                answer=decoded_text,
                bounding_boxes=[box],
                confidence=0.9,
                confidence_tier="high",
                status="success",
                model_used="Qwen2.5-VL-3B-Instruct",
                evidence="Object localized in image coordinates."
            )
        else:
            return SpecialistResponse(
                task="grounding",
                answer=decoded_text,
                confidence=0.0,
                confidence_tier="insufficient",
                status="error",
                error_message="Coordinate parsing failed: model output did not contain valid [x1,y1,x2,y2] pattern"
            )
            
    except Exception as e:
        logger.exception("Exception occurred during grounding execution")
        return SpecialistResponse(
            task="grounding",
            answer="",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=f"Exception during grounding generation: {str(e)}"
        )
