"""
# Run locally only — requires real model download (~6GB). Not run in CI.
Script to manually test VQA, Captioning, and Grounding models.
"""
import os
import urllib.request
from schemas.contracts import SpecialistRequest, ImageMetadata
from models.vqa.vqa import run_vqa
from models.vqa.captioning import run_captioning
from models.vqa.grounding import run_grounding

def main():
    image_path = "test_aerial_image.jpg"
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/320px-Camponotus_flavomarginatus_ant.jpg"
    
    if not os.path.exists(image_path):
        print(f"Downloading test image from {image_url}...")
        urllib.request.urlretrieve(image_url, image_path)
        
    image_metadata = ImageMetadata(
        sensor="unknown",
        crs="EPSG:4326",
        width=320,
        height=320,
        bands=3,
        resolution_m=1.0,
        acquisition_date="2026-01-01T00:00:00Z",
        file_path=image_path
    )
    
    print("\n--- Testing VQA ---")
    request_vqa = SpecialistRequest(query="What is in the image?", images=[image_metadata], task_hint="vqa")
    try:
        resp = run_vqa(request_vqa)
        print(resp)
    except Exception as e:
        print(f"Failed to run VQA: {e}")
        
    print("\n--- Testing Captioning ---")
    request_cap = SpecialistRequest(query="", images=[image_metadata], task_hint="captioning")
    try:
        resp = run_captioning(request_cap)
        print(resp)
    except Exception as e:
        print(f"Failed to run Captioning: {e}")
        
    print("\n--- Testing Grounding ---")
    request_grounding = SpecialistRequest(query="the main subject", images=[image_metadata], task_hint="grounding")
    try:
        resp = run_grounding(request_grounding)
        print(resp)
    except Exception as e:
        print(f"Failed to run Grounding: {e}")

if __name__ == "__main__":
    main()
