"""
SatQuery AI — Automated Evaluation Harness (Person E - Priority 3)

Runs evaluation test set through agent executor and computes summary metrics:
  - Total test cases
  - Success rate
  - Average latency
  - Keyword match rate
"""

import sys
import time
from pathlib import Path
from PIL import Image

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir.resolve()))

from schemas.contracts import ImageMetadata, SpecialistRequest
from agent.executor import Executor
from evaluation.test_set import TEST_SET


def run_evaluation():
    executor = Executor()
    temp_dir = Path("./data/uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)

    img_opt_path = str(temp_dir / "eval_opt.png")
    img_sar_path = str(temp_dir / "eval_sar.png")

    Image.new("RGB", (100, 100), color="green").save(img_opt_path)
    Image.new("RGB", (100, 100), color="gray").save(img_sar_path)

    opt_meta = ImageMetadata(sensor="optical", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path=img_opt_path)
    sar_meta = ImageMetadata(sensor="sar", crs="EPSG:4326", width=100, height=100, resolution_m=10.0, file_path=img_sar_path)

    total = len(TEST_SET)
    successes = 0
    keyword_matches = 0
    latencies = []

    print("==================================================")
    print("SatQuery AI -- Automated Evaluation Runner")
    print("==================================================")

    for item in TEST_SET:
        task_type = item["task_type"]
        query = item["query"]

        if task_type in ("change_detection", "change_vqa"):
            imgs = [opt_meta, opt_meta]
        elif task_type == "optical_sar_fusion":
            imgs = [opt_meta, sar_meta]
        else:
            imgs = [opt_meta]

        req = SpecialistRequest(query=query, images=imgs)

        start = time.monotonic()
        resp, trace = executor.run(req)
        elapsed = time.monotonic() - start
        latencies.append(elapsed)

        is_success = resp.status == "success"
        if is_success:
            successes += 1

        ans_lower = resp.answer.lower()
        match = any(kw.lower() in ans_lower for kw in item["expected_keywords"])
        if match:
            keyword_matches += 1

        status_str = "[PASS]" if is_success else "[FAIL]"
        print(f"{status_str} Test #{item['id']} ({task_type}) - Latency: {elapsed*1000:.1f}ms - Conf: {resp.confidence_tier}")

    avg_lat = (sum(latencies) / total) * 1000 if total > 0 else 0.0
    succ_rate = (successes / total) * 100 if total > 0 else 0.0
    kw_rate = (keyword_matches / total) * 100 if total > 0 else 0.0

    print("==================================================")
    print("EVALUATION SUMMARY")
    print("==================================================")
    print(f"Total Test Cases   : {total}")
    print(f"Success Rate       : {succ_rate:.1f}% ({successes}/{total})")
    print(f"Keyword Match Rate : {kw_rate:.1f}% ({keyword_matches}/{total})")
    print(f"Average Latency    : {avg_lat:.1f} ms")
    print("==================================================")


if __name__ == "__main__":
    run_evaluation()
