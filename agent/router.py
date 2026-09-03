"""
agent/router.py — Rule-Based Intent Classifier / Router

Classifies a (query, images) pair into one of six tool names.

DESIGN RATIONALE (Deterministic Routing)
-----------------------------------------
Classification is done with explicit keyword rules and image-count rules,
NOT with an LLM call. This is intentional for the hackathon phase:

  ✓ Zero inference latency / cost for routing
  ✓ Fully deterministic — same input always picks the same tool
  ✓ Easy to audit and debug — every decision is a readable if-branch
  ✗ Does not handle paraphrase or domain-specific jargon as well as an LLM

# TODO (post-hackathon): replace this rule-based classifier with a fine-tuned
# intent classifier or function-calling LLM call. Keeping this rule-based for
# the hackathon timeline because it is debuggable, deterministic, and has zero
# inference cost/latency.

CLASSIFICATION PRIORITY ORDER
-------------------------------
The rules are checked in strict priority order. Earlier rules win.

a. 2 images, one optical + one sar                     → optical_sar_fusion
b. 2 images, same sensor + change keywords
     + interrogative word (what/where/has/how/?):      → change_vqa
     + no interrogative:                               → change_detection
c. 1 image + grounding keywords                        → ground_region
d. 1 image + description keywords, no question mark    → caption_image
e. 1 image (default)                                   → single_image_vqa
f. Anything else (e.g. 2 images but no optical+SAR
   and no same-sensor):                                → ValueError

KEYWORD DESIGN NOTES
---------------------
Change-indicating keywords: chosen to cover the most common ways users
phrase temporal comparison questions in English. Words like "changed",
"increase", "decrease" are unambiguous change signals; "before/after",
"compare", "difference" signal bi-temporal intent.

Grounding keywords: words that ask the model to spatially locate something
within the image ("where is", "highlight", "locate", "show me"). These are
distinct from VQA questions that happen to ask about location generically.

Description keywords: words that ask for a holistic scene description
without a specific question target. "Describe", "caption", "overview".
"""

import logging
import re

from schemas.contracts import ImageMetadata

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword sets
# ---------------------------------------------------------------------------

# Change-indicating keywords. Indicate that the user wants to compare two
# images over time and reason about what is different.
CHANGE_KEYWORDS: frozenset[str] = frozenset([
    "changed", "change", "changes",
    "increase", "increased", "increasing",
    "decrease", "decreased", "decreasing",
    "compare", "comparison",
    "before", "after",
    "difference", "differ", "different",
    "expand", "expanded", "expansion",
    "grow", "grown", "growth",
    "shrink", "shrunk",
    "new", "lost", "appeared", "disappeared",
    "temporal",
])

# Interrogative signals. If the query also contains one of these, the user
# is asking a specific QUESTION about changes (change_vqa) rather than just
# requesting a change description (change_detection).
INTERROGATIVE_WORDS: frozenset[str] = frozenset([
    "what", "where", "has", "have", "how", "why", "which", "is", "are", "did",
])

# Grounding keywords. Indicate that the user wants to spatially locate a
# region or object within the image and get its pixel coordinates.
GROUNDING_KEYWORDS: frozenset[str] = frozenset([
    "highlight",
    "locate",
    "identify the location",
    "show me",
    "where is",
    "find",
    "point to",
    "bounding box",
    "mark",
    "ground",
    "region of",
    "localise",
    "localize",
])

# Description keywords. Indicate the user wants a holistic scene description.
# Only trigger caption_image when no specific question is asked.
DESCRIPTION_KEYWORDS: frozenset[str] = frozenset([
    "describe",
    "description",
    "what is in this image",
    "caption",
    "overview",
    "summarize",
    "summarise",
    "explain",
    "tell me about",
    "general",
    "what do you see",
    "what can you see",
    "scene",
    "land cover",
])


def _contains_any(text: str, keywords: frozenset[str]) -> bool:
    """
    Return True if text contains any keyword from keywords as a whole word or phrase.

    Uses case-insensitive search with word-boundary awareness for single words.
    Multi-word phrases are checked as plain substrings (after lower-casing).

    Args:
        text: Lower-cased query string.
        keywords: Set of keywords/phrases to search for.
    """
    for kw in keywords:
        if " " in kw:
            # Multi-word phrase — plain substring check is sufficient
            if kw in text:
                return True
        else:
            # Single word — use word boundary to avoid partial matches
            # e.g. "change" should not match "unchanged"
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return True
    return False


def _has_interrogative(text: str) -> bool:
    """
    Return True if the query text contains an interrogative word or a
    literal question mark, indicating the user is asking a specific question.

    Args:
        text: Lower-cased query string.
    """
    if "?" in text:
        return True
    return _contains_any(text, INTERROGATIVE_WORDS)


class Router:
    """
    Deterministic rule-based router.

    Maps (query, images) → one of six tool names:
        "single_image_vqa", "caption_image", "ground_region",
        "change_detection", "change_vqa", "optical_sar_fusion"

    Never calls an LLM. Never uses probabilities. Always returns the same
    tool name for the same input. This determinism is a design requirement,
    not a limitation — it makes routing auditable and reproducible.
    """

    def classify(self, query: str, images: list[ImageMetadata]) -> str:
        """
        Classify (query, images) into a tool name.

        Args:
            query: The user's natural-language question.
            images: List of ImageMetadata for the uploaded image(s).

        Returns:
            One of: "single_image_vqa", "caption_image", "ground_region",
                    "change_detection", "change_vqa", "optical_sar_fusion"

        Raises:
            ValueError: If the combination of image count and types does not
                        match any known tool pattern. The message is descriptive
                        so the caller can surface it to the user.
        """
        q = query.lower().strip()
        n = len(images)

        logger.info(
            "Router.classify called: n_images=%d, query=%r",
            n, query[:80],
        )

        # ------------------------------------------------------------------ #
        # RULE a — Two images, one optical + one SAR → optical_sar_fusion     #
        # ------------------------------------------------------------------ #
        # This rule is checked first regardless of query content, because
        # the image configuration alone determines the correct specialist.
        # An optical+SAR pair can ONLY be meaningfully processed by the
        # fusion specialist.
        if n == 2:
            sensors = [img.sensor.lower() for img in images]
            has_optical = "optical" in sensors
            has_sar = "sar" in sensors

            if has_optical and has_sar:
                logger.info("Route decision: optical_sar_fusion (optical+SAR pair)")
                return "optical_sar_fusion"

            # -------------------------------------------------------------- #
            # RULE b — Two images, same sensor + change keywords              #
            # -------------------------------------------------------------- #
            # Both images have the same sensor type. If the query contains
            # change-indicating keywords, this is a bi-temporal comparison.
            # The distinction between change_vqa and change_detection is
            # whether the user is asking a specific question (interrogative).
            same_sensor = len(set(sensors)) == 1
            if same_sensor:
                if _contains_any(q, CHANGE_KEYWORDS):
                    if _has_interrogative(q):
                        logger.info("Route decision: change_vqa (same-sensor pair + change keywords + interrogative)")
                        return "change_vqa"
                    else:
                        logger.info("Route decision: change_detection (same-sensor pair + change keywords, no interrogative)")
                        return "change_detection"
                # Two same-sensor images but no change keywords — also treat as change_detection
                # since the user uploaded two images of the same type (most likely bi-temporal)
                logger.info("Route decision: change_detection (same-sensor pair, no explicit change keywords — defaulting)")
                return "change_detection"

            # -------------------------------------------------------------- #
            # RULE f (2-image error case)                                     #
            # -------------------------------------------------------------- #
            raise ValueError(
                f"Two images were provided with sensors {sensors}, which does not match "
                "any supported two-image workflow. Supported patterns:\n"
                "  • One 'optical' + one 'sar' image → optical_sar_fusion\n"
                "  • Two images of the same sensor type → change_detection or change_vqa\n"
                "Please check that sensor metadata is correctly set on your images."
            )

        # ------------------------------------------------------------------ #
        # RULE c — Single image + grounding keywords → ground_region          #
        # ------------------------------------------------------------------ #
        # Grounding queries are characterised by spatial-location requests:
        # "where is X", "highlight X", "locate X". These require a different
        # model output format (bounding boxes) vs VQA (text only).
        if n == 1:
            if _contains_any(q, GROUNDING_KEYWORDS):
                logger.info("Route decision: ground_region (grounding keywords detected)")
                return "ground_region"

            # -------------------------------------------------------------- #
            # RULE d — Single image + description keywords, no question mark  #
            # -------------------------------------------------------------- #
            # Description/captioning queries ask for a holistic scene overview
            # rather than answering a specific factual question. The "no
            # question mark" constraint prevents misclassifying queries like
            # "Describe what changes do you see?" as captioning tasks.
            if _contains_any(q, DESCRIPTION_KEYWORDS) and "?" not in q:
                logger.info("Route decision: caption_image (description keywords, no '?')")
                return "caption_image"

            # -------------------------------------------------------------- #
            # RULE e — Single image default → single_image_vqa               #
            # -------------------------------------------------------------- #
            logger.info("Route decision: single_image_vqa (default single-image path)")
            return "single_image_vqa"

        # ------------------------------------------------------------------ #
        # RULE f (edge cases — 0 images or >2 images)                        #
        # ------------------------------------------------------------------ #
        raise ValueError(
            f"Cannot route: received {n} image(s). "
            "SatQuery AI supports 1 image (VQA/captioning/grounding) or "
            "2 images (change detection or optical-SAR fusion). "
            "Please upload 1 or 2 images."
        )
