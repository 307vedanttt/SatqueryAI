"""
SatQuery AI — Deterministic Router (Person A)

Provides priority-based, deterministic classification mapping
(query, list[ImageMetadata]) to one of six fixed tool names:
  1. optical_sar_fusion
  2. change_vqa
  3. change_detection
  4. ground_region
  5. caption_image
  6. single_image_vqa

Rationale for Keyword Lists:
- Change indicators: 'changed', 'increase', 'decrease', 'compare', 'before', 'after', 'difference'
  reflect bi-temporal comparison queries.
- Question indicators: '?', 'what', 'where', 'has', 'how' distinguish change VQA from general change detection.
- Grounding keywords: 'highlight', 'where is', 'locate', 'identify the location of', 'show me'
  signal region bounding box requests.
- Description keywords: 'describe', 'what is in this image', 'caption' without specific questions signal global scene summaries.
"""

import re
from schemas.contracts import ImageMetadata

# TODO (post-hackathon): replace this rule-based classifier with a fine-tuned intent classifier
# or function-calling LLM call. Keeping this rule-based for the hackathon timeline because it is
# debuggable, deterministic, and has zero inference cost/latency.

CHANGE_KEYWORDS = {"changed", "increase", "decrease", "compare", "before", "after", "difference"}
INTERROGATIVE_KEYWORDS = {"what", "where", "has", "how"}
GROUNDING_KEYWORDS = {"highlight", "where is", "locate", "identify the location of", "show me"}
DESCRIPTION_KEYWORDS = {"describe", "what is in this image", "caption"}


class Router:
    """Deterministic intent router."""

    def classify(self, query: str, images: list[ImageMetadata]) -> str:
        """
        Classify the query and image configuration into one of 6 tool names.
        
        Priority Rules:
        a. 2 images (1 optical + 1 SAR) -> optical_sar_fusion
        b. 2 images (same sensor) + change keywords -> change_vqa (if question) else change_detection
        c. 1 image + grounding keywords -> ground_region
        d. 1 image + description keywords (no specific question) -> caption_image
        e. 1 image (default) -> single_image_vqa
        f. Otherwise -> raise ValueError
        """
        n_images = len(images)
        query_lower = query.lower().strip()

        # Rule A: 2 images (1 optical + 1 SAR)
        if n_images == 2:
            sensors = {(img.sensor or "").lower() for img in images}
            if "optical" in sensors and "sar" in sensors:
                return "optical_sar_fusion"

        # Rule B: 2 images (same sensor) + change keywords
        if n_images == 2:
            s1, s2 = (images[0].sensor or "").lower(), (images[1].sensor or "").lower()
            if s1 == s2 and s1 != "":
                has_change_kw = any(kw in query_lower for kw in CHANGE_KEYWORDS)
                if has_change_kw or not query_lower:
                    is_question = ("?" in query_lower) or any(
                        re.search(r"\b" + kw + r"\b", query_lower) for kw in INTERROGATIVE_KEYWORDS
                    )
                    return "change_vqa" if is_question else "change_detection"

        # Rule C: 1 image + grounding keywords
        if n_images == 1:
            if any(kw in query_lower for kw in GROUNDING_KEYWORDS):
                return "ground_region"

        # Rule D: 1 image + description keywords (no specific question)
        if n_images == 1:
            has_desc_kw = any(kw in query_lower for kw in DESCRIPTION_KEYWORDS)
            has_question_mark = "?" in query_lower
            if has_desc_kw and not has_question_mark:
                return "caption_image"

        # Rule E: 1 image default -> single_image_vqa
        if n_images == 1:
            return "single_image_vqa"

        # Rule F: No clean match -> raise ValueError
        raise ValueError(
            f"Unable to route query: {n_images} image(s) provided. "
            "Input does not match single-image, valid bi-temporal pair, or optical+SAR pair criteria."
        )
