"""
frontend/app.py — Gradio Blocks Demo UI for SatQuery AI

ARCHITECTURE
------------
This Gradio app calls agent.executor.Executor.run() DIRECTLY (no HTTP),
using the shared schemas/contracts.py types and remote_sensing image loading.
This is deliberately simpler than going through the FastAPI backend — during
demo day, fewer moving parts = fewer failure modes.

The app handles:
  1. 1 or 2 uploaded images (PIL fallback via load_benchmark_image)
  2. Natural-language query text
  3. Routes through the bounded executor (MAX_STEPS=6)
  4. Shows: answer, confidence badge, bbox overlay, execution trace

STUB vs REAL MODEL
------------------
Out of the box, the executor uses STUB callables (returns placeholder answers).
Once models/vqa/vqa.py is merged and the model is downloaded (~6GB), swap the
stub with one call (see SWAP INSTRUCTIONS below).

No UI changes are needed when real models are integrated — the Gradio code
only reads the SpecialistResponse and ExecutionTrace contracts.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

import gradio as gr
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Make repo root importable (handles both `cd frontend && python app.py`
# and `python frontend/app.py` launch styles)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agent.executor import Executor
from agent.trace import format_trace_for_display
from remote_sensing.geotiff import load_benchmark_image
from schemas.contracts import ImageMetadata, SpecialistRequest, SpecialistResponse, ExecutionTrace

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SWAP INSTRUCTIONS — replace stubs with real models once they are merged:
#
#   from agent.registry import ToolRegistry
#   from models.vqa.vqa import run_vqa
#   from models.vqa.captioning import run_captioning
#   from models.vqa.grounding import run_grounding
#
#   registry = ToolRegistry()
#   registry.register_tool("single_image_vqa", run_vqa,
#       registry._tools["single_image_vqa"]["precondition"])
#   registry.register_tool("caption_image", run_captioning,
#       registry._tools["caption_image"]["precondition"])
#   registry.register_tool("ground_region", run_grounding,
#       registry._tools["ground_region"]["precondition"])
#   executor = Executor(registry=registry)
#
# ---------------------------------------------------------------------------
executor = Executor()  # Uses stubs by default


# ---------------------------------------------------------------------------
# Confidence badge
# ---------------------------------------------------------------------------

_BADGE_MAP = {
    "high":         "🟢 HIGH — Strong evidence from the model.",
    "moderate":     "🟡 MODERATE — Answer likely correct; treat with caution.",
    "insufficient": "🔴 INSUFFICIENT — Low confidence; results may be unreliable.",
}


def _confidence_badge(tier: str) -> str:
    return _BADGE_MAP.get(tier, f"❓ {tier.upper()}")


# ---------------------------------------------------------------------------
# Bounding box overlay
# ---------------------------------------------------------------------------

def _draw_bboxes(pil_image: Image.Image, bboxes: list) -> Image.Image:
    """
    Draw bounding boxes from SpecialistResponse.bounding_boxes on the image.

    Coordinates are assumed to be normalised 0–1000 (Qwen2.5-VL convention).
    We scale them to pixel coordinates before drawing.

    Args:
        pil_image: The original PIL image.
        bboxes: List of BoundingBox objects from SpecialistResponse.

    Returns:
        A new PIL image with boxes drawn in bright red with labels.
    """
    if not bboxes:
        return pil_image

    img = pil_image.convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    W, H = img.size

    for bbox in bboxes:
        # Scale from 0–1000 normalised space to pixel coordinates
        x1 = int(bbox.x1 / 1000 * W)
        y1 = int(bbox.y1 / 1000 * H)
        x2 = int(bbox.x2 / 1000 * W)
        y2 = int(bbox.y2 / 1000 * H)

        # Draw rectangle
        draw.rectangle([x1, y1, x2, y2], outline=(255, 50, 50), width=3)

        # Draw label background and text
        label = bbox.label or "detected"
        conf_str = f" ({bbox.confidence:.0%})" if bbox.confidence > 0 else ""
        text = f"{label}{conf_str}"

        # Simple label above the box
        draw.rectangle([x1, max(0, y1 - 20), x1 + len(text) * 7 + 4, y1], fill=(255, 50, 50))
        draw.text((x1 + 2, max(0, y1 - 18)), text, fill=(255, 255, 255))

    return img


# ---------------------------------------------------------------------------
# Image loading helper
# ---------------------------------------------------------------------------

def _load_pil_and_meta(file_path: str, sensor: str = "optical") -> tuple[Image.Image, ImageMetadata]:
    """
    Load an image from disk via PIL and return (PIL.Image, ImageMetadata).

    Uses load_benchmark_image() from remote_sensing.geotiff which sets
    crs="none" for benchmark data — correct for any image uploaded via the UI
    since we have no geospatial context from the file picker.

    Args:
        file_path: Path returned by Gradio's file upload component.
        sensor: Sensor type to assign ("optical" default for UI uploads).

    Returns:
        (PIL.Image, ImageMetadata) tuple.
    """
    _, meta = load_benchmark_image(file_path, sensor)
    pil_img = Image.open(file_path).convert("RGB")
    return pil_img, meta


def _guess_sensor_from_filename(path: str) -> str:
    """
    Heuristic: return 'sar' if filename contains SAR hint, else 'optical'.
    """
    lower = path.lower()
    for hint in ("sar", "s1_", "sentinel-1", "sentinel1"):
        if hint in lower:
            return "sar"
    return "optical"


# ---------------------------------------------------------------------------
# Core analysis function — wired to the Analyze button
# ---------------------------------------------------------------------------

def analyze(
    image1_path: Optional[str],
    image2_path: Optional[str],
    query: str,
) -> tuple[str, str, Optional[Image.Image], str]:
    """
    Main analysis function called by the Gradio Analyze button.

    Args:
        image1_path: Path to first uploaded image (required).
        image2_path: Path to second uploaded image (optional).
        query: User's natural-language question.

    Returns:
        Tuple of (answer_text, confidence_badge, result_image, trace_text).
    """
    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------
    if not image1_path:
        return (
            "⚠️ Please upload at least one image.",
            _confidence_badge("insufficient"),
            None,
            "No analysis performed — no image provided.",
        )

    if not query or not query.strip():
        return (
            "⚠️ Please enter a question or description.",
            _confidence_badge("insufficient"),
            None,
            "No analysis performed — no query provided.",
        )

    # ------------------------------------------------------------------
    # Load images
    # ------------------------------------------------------------------
    images: list[ImageMetadata] = []
    pil_images: list[Image.Image] = []

    try:
        sensor1 = _guess_sensor_from_filename(image1_path)
        pil1, meta1 = _load_pil_and_meta(image1_path, sensor1)
        images.append(meta1)
        pil_images.append(pil1)
    except Exception as exc:
        return (
            f"❌ Error loading image 1: {exc}",
            _confidence_badge("insufficient"),
            None,
            f"Image loading failed: {exc}",
        )

    if image2_path:
        try:
            sensor2 = _guess_sensor_from_filename(image2_path)
            pil2, meta2 = _load_pil_and_meta(image2_path, sensor2)
            images.append(meta2)
            pil_images.append(pil2)
        except Exception as exc:
            return (
                f"❌ Error loading image 2: {exc}",
                _confidence_badge("insufficient"),
                None,
                f"Image 2 loading failed: {exc}",
            )

    # ------------------------------------------------------------------
    # Build request and run executor
    # ------------------------------------------------------------------
    request = SpecialistRequest(query=query, images=images)

    try:
        response, trace = executor.run(request)
    except Exception as exc:
        logger.exception("Executor raised unexpected exception")
        return (
            f"❌ Internal error: {exc}",
            _confidence_badge("insufficient"),
            pil_images[0] if pil_images else None,
            f"Executor failed with unexpected exception: {exc}",
        )

    # ------------------------------------------------------------------
    # Build output components
    # ------------------------------------------------------------------

    # 1. Answer text
    if response.status == "error":
        answer_text = f"❌ Analysis failed:\n{response.error_message}"
    else:
        answer_text = response.answer

    # 2. Confidence badge
    badge = _confidence_badge(response.confidence_tier)

    # 3. Bounding-box overlay on first image
    result_img: Optional[Image.Image] = None
    if pil_images:
        if response.bounding_boxes:
            result_img = _draw_bboxes(pil_images[0], response.bounding_boxes)
        else:
            result_img = pil_images[0]

    # 4. Execution trace
    trace_text = format_trace_for_display(trace)

    return answer_text, badge, result_img, trace_text


# ---------------------------------------------------------------------------
# Gradio Blocks layout
# ---------------------------------------------------------------------------

_TITLE = "🛰️ SatQuery AI — Remote Sensing Vision-Language Assistant"
_DESC = (
    "**Smart India Hackathon 2026 · Problem SIH26167 · ISRO** — "
    "Upload 1 or 2 satellite images and ask a natural-language question. "
    "The system routes your query to the appropriate specialist model and "
    "shows a full auditable execution trace."
)
_EXAMPLE_QUERIES = [
    "Describe the land cover and major objects visible in this image.",
    "How many water bodies are visible in the image?",
    "Highlight the largest urban area in this scene.",
    "Has the vegetation changed between these two images?",
    "What flooded areas can be identified by combining both sensor types?",
]

with gr.Blocks(
    title="SatQuery AI",
    theme=gr.themes.Base(
        primary_hue="blue",
        secondary_hue="cyan",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    ),
    css="""
    .title-block { text-align: center; padding: 1rem 0; }
    .output-label { font-weight: 600; font-size: 0.85rem; color: #64748b;
                    text-transform: uppercase; letter-spacing: 0.05em; }
    .badge-text { font-size: 1.1rem; font-weight: 700; }
    """,
) as demo:

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    with gr.Row(elem_classes="title-block"):
        gr.Markdown(f"# {_TITLE}\n{_DESC}")

    # ------------------------------------------------------------------
    # Main layout: left (inputs) | right (outputs)
    # ------------------------------------------------------------------
    with gr.Row():
        # ---- LEFT COLUMN: inputs ----
        with gr.Column(scale=4):
            gr.Markdown("### 📁 Upload Images")
            with gr.Row():
                image1 = gr.Image(
                    label="Image 1 (required)",
                    type="filepath",
                    sources=["upload"],
                    elem_id="image1",
                )
                image2 = gr.Image(
                    label="Image 2 (optional — for change detection or optical+SAR fusion)",
                    type="filepath",
                    sources=["upload"],
                    elem_id="image2",
                )

            gr.Markdown("### 💬 Your Question")
            query_box = gr.Textbox(
                label="Query",
                placeholder="e.g. Describe the land cover and major objects visible in this image.",
                lines=3,
                max_lines=6,
                elem_id="query_box",
            )

            gr.Markdown("**Quick query suggestions:**")
            with gr.Row():
                for i, eq in enumerate(_EXAMPLE_QUERIES[:3]):
                    gr.Button(f"📝 {eq[:40]}…", size="sm", elem_id=f"example_{i}").click(
                        fn=lambda q=eq: q, outputs=query_box
                    )
            with gr.Row():
                for i, eq in enumerate(_EXAMPLE_QUERIES[3:]):
                    gr.Button(f"📝 {eq[:40]}…", size="sm", elem_id=f"example_r2_{i}").click(
                        fn=lambda q=eq: q, outputs=query_box
                    )

            analyze_btn = gr.Button(
                "🔍 Analyze Imagery",
                variant="primary",
                size="lg",
                elem_id="analyze_btn",
            )

        # ---- RIGHT COLUMN: outputs ----
        with gr.Column(scale=6):
            gr.Markdown("### 📊 Analysis Results")

            answer_out = gr.Textbox(
                label="Answer",
                lines=5,
                interactive=False,
                elem_id="answer_out",
                show_copy_button=True,
            )

            badge_out = gr.Textbox(
                label="Confidence",
                interactive=False,
                elem_id="badge_out",
                elem_classes="badge-text",
            )

            result_img_out = gr.Image(
                label="Result Image (with bounding boxes if grounding was performed)",
                type="pil",
                interactive=False,
                elem_id="result_img",
            )

            with gr.Accordion("🔍 Execution Trace (Auditable Reasoning Chain)", open=False):
                trace_out = gr.Textbox(
                    label="Step-by-step trace",
                    lines=15,
                    interactive=False,
                    elem_id="trace_out",
                    show_copy_button=True,
                    font_size=13,
                )

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    gr.Markdown(
        "---\n"
        "*SatQuery AI · Smart India Hackathon 2026 · Problem SIH26167 · ISRO* · "
        "Built with ❤️ using Gradio, FastAPI, Qwen2.5-VL, and PyTorch"
    )

    # ------------------------------------------------------------------
    # Wire the Analyze button
    # ------------------------------------------------------------------
    analyze_btn.click(
        fn=analyze,
        inputs=[image1, image2, query_box],
        outputs=[answer_out, badge_out, result_img_out, trace_out],
        api_name="analyze",
    )


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SatQuery AI Gradio Demo")
    parser.add_argument("--port", type=int, default=7860, help="Port to serve on")
    parser.add_argument("--share", action="store_true", help="Create a public share link")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    print("=" * 65)
    print(" SatQuery AI — Gradio Demo")
    print(f" URL: http://localhost:{args.port}")
    print(" Mode: STUB responses (real model: install torch + transformers)")
    print("=" * 65)

    demo.launch(
        server_port=args.port,
        share=args.share,
        show_error=True,
        quiet=False,
    )
