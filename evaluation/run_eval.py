"""Evaluation runner for SatQuery AI."""

import os
import time
import logging
from collections import defaultdict
from typing import Dict, Any, List

from evaluation.test_set import get_test_cases
from schemas.contracts import ImageMetadata, SpecialistRequest
from agent.executor import Executor

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_evaluation(verbose: bool = True) -> None:
    """Run the evaluation suite over curated test cases."""
    test_cases = get_test_cases()
    
    total_cases = len(test_cases)
    cases_run = 0
    cases_skipped = 0
    success_count = 0
    keyword_match_count = 0
    total_latency = 0.0
    
    # Metrics by task type
    task_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        'run': 0, 'success': 0, 'keyword_match': 0, 'latency': 0.0
    })
    
    executor = Executor()
    
    for i, tc in enumerate(test_cases, 1):
        image_paths = tc.get("image_paths", [])
        
        # Check if all images exist
        missing_images = [p for p in image_paths if not os.path.exists(p)]
        if missing_images:
            logger.warning(f"Skipping test case {i} due to missing images: {missing_images}")
            cases_skipped += 1
            continue
            
        cases_run += 1
        task_type = tc["task_type"]
        task_metrics[task_type]['run'] += 1
        
        # Construct ImageMetadata
        images = []
        for path, sensor in zip(image_paths, tc.get("sensors", ["optical"] * len(image_paths))):
            images.append(
                ImageMetadata(
                    sensor=sensor,
                    file_path=path,
                    crs="EPSG:4326",  # placeholder
                    width=1024,      # placeholder
                    height=1024,     # placeholder
                    bands=3,         # placeholder
                    resolution_m=1.0 # placeholder
                )
            )
            
        request = SpecialistRequest(
            query=tc["query"],
            images=images,
            task_hint=task_type
        )
        
        start_time = time.time()
        try:
            response = executor.run(request)
            latency = time.time() - start_time
            
            is_success = (response.status == "success")
            
            answer_lower = response.answer.lower() if response.answer else ""
            has_keyword = any(kw.lower() in answer_lower for kw in tc.get("expected_keywords", []))
            
            if is_success:
                success_count += 1
                task_metrics[task_type]['success'] += 1
                
            if has_keyword:
                keyword_match_count += 1
                task_metrics[task_type]['keyword_match'] += 1
                
            total_latency += latency
            task_metrics[task_type]['latency'] += latency
            
            if verbose:
                logger.info(f"Test case {i} ({task_type}) - Success: {is_success}, Latency: {latency:.2f}s")
                
        except Exception as e:
            latency = time.time() - start_time
            total_latency += latency
            task_metrics[task_type]['latency'] += latency
            logger.error(f"Test case {i} failed with exception: {e}")

    # Generate summary table
    print("\n============================================================")
    print("SatQuery AI Evaluation Summary")
    print("============================================================")
    print(f"Total cases:        {total_cases}")
    print(f"Cases run:          {cases_run}  ({cases_skipped} skipped — missing image files)")
    
    if cases_run > 0:
        success_rate = (success_count / cases_run) * 100
        keyword_match_rate = (keyword_match_count / cases_run) * 100
        avg_latency = total_latency / cases_run
        
        print(f"Success rate:       {success_rate:.1f}% ({success_count}/{cases_run})")
        print(f"Keyword match rate: {keyword_match_rate:.1f}% ({keyword_match_count}/{cases_run})")
        print(f"Avg latency:        {avg_latency:.2f}s")
        
        print("\nBy task type:")
        for t_type, metrics in task_metrics.items():
            t_run = metrics['run']
            if t_run > 0:
                t_success = metrics['success']
                t_keyword = metrics['keyword_match']
                t_latency = metrics['latency'] / t_run
                print(f"  {t_type:<18}: {t_success}/{t_run} success, {t_keyword}/{t_run} keyword match, {t_latency:.2f}s")
    else:
        print("\nNo cases were run. Ensure test images exist in the data/ directory.")
        
    print("============================================================\n")

if __name__ == '__main__':
    run_evaluation()
