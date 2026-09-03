"""
SatQuery AI — Image Captioning Specialist (Person B)

Overrides user query with standard scene description prompt:
"Describe the land cover and major objects visible in this image."
"""

import logging
from schemas.contracts import SpecialistRequest, SpecialistResponse
from models.vqa.vqa import run_vqa

logger = logging.getLogger("satquery.models.vqa.captioning")

CAPTION_PROMPT = "Describe the land cover and major objects visible in this image."


def run_captioning(request: SpecialistRequest) -> SpecialistResponse:
    """Run image captioning by overriding query with standard scene description prompt."""
    caption_request = SpecialistRequest(
        query=CAPTION_PROMPT,
        images=request.images,
        task_hint="captioning",
    )
    resp = run_vqa(caption_request)
    resp.task = "captioning"
    return resp
