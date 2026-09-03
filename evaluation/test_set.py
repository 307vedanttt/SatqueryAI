"""
SatQuery AI — Curated Test Set (Person E - Priority 3)
"""

TEST_SET = [
    {
        "id": 1,
        "query": "Describe the land cover and major objects visible in this image.",
        "task_type": "captioning",
        "expected_keywords": ["land cover", "vegetation", "objects", "water"],
    },
    {
        "id": 2,
        "query": "What is the primary feature visible?",
        "task_type": "vqa",
        "expected_keywords": ["feature", "region"],
    },
    {
        "id": 3,
        "query": "Highlight the largest building in this image.",
        "task_type": "grounding",
        "expected_keywords": ["bounding box", "grounded", "building"],
    },
    {
        "id": 4,
        "query": "Has the built-up area increased between these dates?",
        "task_type": "change_vqa",
        "expected_keywords": ["change", "bi-temporal", "magnitude"],
    },
    {
        "id": 5,
        "query": "Detect changes between before and after image",
        "task_type": "change_detection",
        "expected_keywords": ["change", "magnitude", "difference"],
    },
    {
        "id": 6,
        "query": "Fuse optical and SAR imagery to identify structures.",
        "task_type": "optical_sar_fusion",
        "expected_keywords": ["fusion", "optical", "sar"],
    },
]
