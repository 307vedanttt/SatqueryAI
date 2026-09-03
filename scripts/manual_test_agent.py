"""
scripts/manual_test_agent.py — Manual End-to-End Agent Test

Constructs 5 different sample SpecialistRequest objects and runs each
through Executor.run(), printing the formatted execution trace for each.

This script is the acceptance-criteria validation for Person A:
"A manual script that constructs 5 different sample SpecialistRequest
objects and runs each through Executor.run(), printing the formatted
trace for each — run this and confirm the routing decisions look
correct by eye."

Usage:
    python scripts/manual_test_agent.py

Expected output:
    For each of the 5 requests, you should see:
      - The query and detected intent tool
      - A numbered list of execution steps
      - Final confidence tier
      - Total steps / 6 maximum

All 5 tests should route to the CORRECT tool as labelled.
"""

import logging
import sys
import os

# Make repo root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Configure logging at WARNING level so only important messages appear
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s | %(name)s | %(message)s",
)

from agent.executor import Executor
from agent.trace import format_trace_for_display
from schemas.contracts import ImageMetadata, SpecialistRequest


# ---------------------------------------------------------------------------
# Sample image metadata — these represent typical inputs a user might upload.
# The file paths don't need to exist for the STUB-based test to work.
# ---------------------------------------------------------------------------

def _optical_image(path: str, crs: str = "EPSG:4326", res: float = 10.0) -> ImageMetadata:
    return ImageMetadata(
        sensor="optical",
        crs=crs,
        width=10980,
        height=10980,
        bands=4,
        resolution_m=res,
        acquisition_date="2024-06-15",
        file_path=path,
    )


def _sar_image(path: str, crs: str = "EPSG:4326", res: float = 10.0) -> ImageMetadata:
    return ImageMetadata(
        sensor="sar",
        crs=crs,
        width=10000,
        height=10000,
        bands=2,
        resolution_m=res,
        acquisition_date="2024-06-16",
        file_path=path,
    )


# ---------------------------------------------------------------------------
# Five sample requests — one per major routing scenario
# ---------------------------------------------------------------------------

SAMPLE_REQUESTS: list[tuple[str, SpecialistRequest]] = [
    # --- Test 1: Single-image VQA (default single-image path) ---
    (
        "Expected route: single_image_vqa",
        SpecialistRequest(
            query="How many reservoirs are visible in this satellite image?",
            images=[_optical_image("/data/sentinel2_mumbai_2024.tif")],
        ),
    ),

    # --- Test 2: Image captioning (description keyword, no question mark) ---
    (
        "Expected route: caption_image",
        SpecialistRequest(
            query="Describe the land cover and major objects visible in this image",
            images=[_optical_image("/data/cartosat_delhi_2024.tif")],
        ),
    ),

    # --- Test 3: Region grounding ---
    (
        "Expected route: ground_region",
        SpecialistRequest(
            query="Highlight the largest urban settlement in this aerial photograph",
            images=[_optical_image("/data/resourcesat_urban.tif")],
        ),
    ),

    # --- Test 4: Bi-temporal change VQA ---
    (
        "Expected route: change_vqa",
        SpecialistRequest(
            query="Has the water body decreased between these two dates?",
            images=[
                _optical_image("/data/sentinel2_lake_2023.tif"),
                _optical_image("/data/sentinel2_lake_2024.tif"),
            ],
        ),
    ),

    # --- Test 5: Optical-SAR fusion ---
    (
        "Expected route: optical_sar_fusion",
        SpecialistRequest(
            query="Identify the flooded agricultural areas combining both sensor types",
            images=[
                _optical_image("/data/sentinel2_flood_optical.tif", "EPSG:32644", 10.0),
                _sar_image("/data/sentinel1_flood_sar.tif", "EPSG:32644", 10.0),
            ],
        ),
    ),
]


def run_manual_tests() -> None:
    """Run all 5 sample requests through the executor and print formatted traces."""
    executor = Executor()
    separator = "=" * 70

    print(separator)
    print(" SatQuery AI — Manual Agent Test (5 Sample Requests)")
    print(" All tools are STUBS — responses are placeholder text.")
    print(" Focus on verifying routing decisions are correct.")
    print(separator)
    print()

    all_passed = True

    for i, (expected_label, request) in enumerate(SAMPLE_REQUESTS, start=1):
        print(f"{'─' * 70}")
        print(f" REQUEST {i}/5 — {expected_label}")
        print(f"{'─' * 70}")

        response, trace = executor.run(request)

        # Print the formatted trace (this is the key deliverable for the demo UI)
        print(format_trace_for_display(trace))
        print()

        # Print response summary
        print(f"Response status:     {response.status}")
        print(f"Response task:       {response.task}")
        print(f"Confidence tier:     {response.confidence_tier}")
        if response.status == "error":
            print(f"Error message:       {response.error_message}")
            all_passed = False
        else:
            print(f"Answer (first 80c): {response.answer[:80]}...")
        print()

    print(separator)
    if all_passed:
        print(" ✅ All 5 requests completed successfully.")
        print(" Verify routing decisions match the 'Expected route' labels above.")
    else:
        print(" ⚠️  One or more requests returned an error. Review trace above.")
    print(separator)


if __name__ == "__main__":
    run_manual_tests()
