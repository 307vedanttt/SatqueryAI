"""
SatQuery AI — Manual Test Agent Script (Person A)

Runs 5 sample SpecialistRequest queries through Executor.run() and prints formatted traces.
"""

import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir.resolve()))

from schemas.contracts import ImageMetadata, SpecialistRequest
from agent.executor import Executor
from agent.trace import format_trace_for_display


def run_manual_tests():
    executor = Executor()

    # 1. Single Optical VQA
    req1 = SpecialistRequest(
        query="What is the primary land cover visible?",
        images=[
            ImageMetadata(sensor="optical", crs="EPSG:4326", width=1024, height=1024, resolution_m=10.0, file_path="/tmp/img1.tif")
        ],
    )

    # 2. Grounding Query
    req2 = SpecialistRequest(
        query="Highlight the largest reservoir in this image.",
        images=[
            ImageMetadata(sensor="optical", crs="EPSG:4326", width=1024, height=1024, resolution_m=10.0, file_path="/tmp/img1.tif")
        ],
    )

    # 3. Bi-Temporal Change Detection
    req3 = SpecialistRequest(
        query="Has the built-up area increased between these dates?",
        images=[
            ImageMetadata(sensor="optical", crs="EPSG:4326", width=1024, height=1024, resolution_m=10.0, file_path="/tmp/t1.tif"),
            ImageMetadata(sensor="optical", crs="EPSG:4326", width=1024, height=1024, resolution_m=10.0, file_path="/tmp/t2.tif"),
        ],
    )

    # 4. Optical-SAR Multimodal Fusion
    req4 = SpecialistRequest(
        query="Use both sensors to detect urban structures.",
        images=[
            ImageMetadata(sensor="optical", crs="EPSG:4326", width=1024, height=1024, resolution_m=10.0, file_path="/tmp/opt.tif"),
            ImageMetadata(sensor="sar", crs="EPSG:4326", width=1024, height=1024, resolution_m=10.0, file_path="/tmp/sar.tif"),
        ],
    )

    # 5. Invalid Precondition (Change detection on 1 image)
    req5 = SpecialistRequest(
        query="Show changes between images",
        images=[
            ImageMetadata(sensor="optical", crs="EPSG:4326", width=1024, height=1024, resolution_m=10.0, file_path="/tmp/img1.tif")
        ],
    )

    requests = [req1, req2, req3, req4, req5]

    for idx, r in enumerate(requests, 1):
        print(f"\n==========================================")
        print(f"  MANUAL TEST CASE {idx}")
        print(f"==========================================")
        resp, trace = executor.run(r)
        print(format_trace_for_display(trace))
        print(f"Status: {resp.status} | Task: {resp.task}")
        print(f"Answer: {resp.answer}")


if __name__ == "__main__":
    run_manual_tests()
