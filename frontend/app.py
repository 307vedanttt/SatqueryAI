"""
SatQuery AI — Gradio UI POC (Person E - Priority 1)

Runs Gradio Blocks interface with:
  - 1 or 2 image upload
  - Text query input
  - Answer output
  - Colored confidence tier badge
  - Bounding box overlay drawing on PIL Image
  - Expandable Execution Trace accordion
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir.resolve()))

import gradio as gr
from schemas.contracts import ImageMetadata, SpecialistRequest
from agent.executor import Executor
from agent.trace import format_trace_for_display

executor = Executor()


def annotate_image_with_bboxes(pil_img: Image.Image, bboxes: list) -> Image.Image:
    """Draw bounding box overlays on PIL image."""
    annotated = pil_img.copy()
    draw = ImageDraw.Draw(annotated)
    w, h = annotated.size

    for box in bboxes:
        # Check if normalized 0-1000 or 0-1
        if box.xmax <= 1.0 and box.ymax <= 1.0:
            xmin, xmax = box.xmin * w, box.xmax * w
            ymin, ymax = box.ymin * h, box.ymax * h
        elif box.xmax <= 1000.0 and box.ymax <= 1000.0:
            xmin, xmax = (box.xmin / 1000.0) * w, (box.xmax / 1000.0) * w
            ymin, ymax = (box.ymin / 1000.0) * h, (box.ymax / 1000.0) * h
        else:
            xmin, ymin, xmax, ymax = box.xmin, box.ymin, box.xmax, box.ymax

        draw.rectangle([xmin, ymin, xmax, ymax], outline="red", width=4)
        draw.text((xmin + 4, ymin + 4), box.label, fill="red")

    return annotated


def process_query(files, query: str):
    if not files or len(files) == 0:
        return (
            "Error: Please upload at least 1 image.",
            "🔴 Insufficient Evidence",
            None,
            "No trace generated.",
        )

    if not query or not query.strip():
        query = "Describe the land cover and major objects visible in this image."

    # Build ImageMetadata list
    images_meta = []
    for f in files:
        file_path = f.name if hasattr(f, "name") else str(f)
        sensor = "sar" if "sar" in file_path.lower() or "s1" in file_path.lower() else "optical"
        images_meta.append(
            ImageMetadata(
                sensor=sensor,
                crs="EPSG:4326",
                width=1024,
                height=1024,
                resolution_m=10.0,
                file_path=file_path,
            )
        )

    req = SpecialistRequest(query=query.strip(), images=images_meta)
    resp, trace = executor.run(req)

    # Format confidence badge
    tier = (resp.confidence_tier or "insufficient").lower()
    if tier == "high":
        badge = "🟢 High Confidence (Score: {:.2f})".format(resp.confidence)
    elif tier == "moderate":
        badge = "🟡 Moderate Confidence (Score: {:.2f})".format(resp.confidence)
    elif tier == "low":
        badge = "🟠 Low Confidence (Score: {:.2f})".format(resp.confidence)
    else:
        badge = "🔴 Insufficient Evidence"

    # Handle image annotation
    try:
        first_img = Image.open(images_meta[0].file_path).convert("RGB")
        if resp.bounding_boxes and len(resp.bounding_boxes) > 0:
            out_img = annotate_image_with_bboxes(first_img, resp.bounding_boxes)
        else:
            out_img = first_img
    except Exception:
        out_img = None

    trace_str = format_trace_for_display(trace)

    return resp.answer, badge, out_img, trace_str


# Build Gradio UI
with gr.Blocks(title="SatQuery AI — SIH 2026 Demo", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🛰️ SatQuery AI — Remote Sensing Assistant")
    gr.Markdown("**ISRO Problem Statement SIH26167 — SIH 2026** | *\"Don't choose the model. Ask the question.\"*")

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(
                label="Upload Satellite/Aerial Imagery (1 or 2 images)",
                file_count="multiple",
                file_types=[".tif", ".tiff", ".png", ".jpg", ".jpeg"],
            )
            query_input = gr.Textbox(
                label="Natural Language Query",
                placeholder="Describe the land cover and major objects visible in this image.",
                lines=3,
            )
            analyze_btn = gr.Button("⚡ Run Agentic Analysis", variant="primary")

        with gr.Column(scale=1):
            answer_output = gr.Textbox(label="Generated Answer", lines=5)
            confidence_badge = gr.Markdown("### Confidence Badge")
            image_output = gr.Image(label="Visual Output / Bounding Box Grounding")

    with gr.Accordion("⚙️ Auditable Execution Trace", open=True):
        trace_output = gr.Code(label="Step-by-Step Execution Log", language=None, lines=10)

    analyze_btn.click(
        fn=process_query,
        inputs=[file_input, query_input],
        outputs=[answer_output, confidence_badge, image_output, trace_output],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
