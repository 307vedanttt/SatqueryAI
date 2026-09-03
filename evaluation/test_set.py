"""Curated test cases for SatQuery AI evaluation."""

TEST_CASES = [
    {
        "image_paths": ["data/sample_optical.jpg"],
        "query": "Describe the land cover and major objects visible in this image.",
        "expected_keywords": ["land", "cover", "vegetation", "urban", "water"],
        "task_type": "caption_image",
        "n_images": 1,
        "sensors": ["optical"],
    },
    {
        "image_paths": ["data/sample_sar.tif"],
        "query": "Is there any ship visible in this SAR image?",
        "expected_keywords": ["ship", "vessel", "water", "no", "yes"],
        "task_type": "single_image_vqa",
        "n_images": 1,
        "sensors": ["sar"],
    },
    {
        "image_paths": ["data/sample_multispectral.tif"],
        "query": "Locate the airports in the image.",
        "expected_keywords": ["airport", "runway", "located"],
        "task_type": "object_detection",
        "n_images": 1,
        "sensors": ["multispectral"],
    },
    {
        "image_paths": ["data/pre_disaster.tif", "data/post_disaster.tif"],
        "query": "Compare these two images and assess the damage caused by the flood.",
        "expected_keywords": ["flood", "water", "damage", "inundated", "change"],
        "task_type": "change_detection",
        "n_images": 2,
        "sensors": ["optical", "optical"],
    },
    {
        "image_paths": ["data/sample_hyper.tif"],
        "query": "What type of crops are planted in the central fields?",
        "expected_keywords": ["crop", "agriculture", "wheat", "corn", "rice"],
        "task_type": "single_image_vqa",
        "n_images": 1,
        "sensors": ["hyperspectral"],
    },
    {
        "image_paths": ["data/urban_area.jpg"],
        "query": "Count the number of residential buildings.",
        "expected_keywords": ["building", "residential", "count", "number"],
        "task_type": "single_image_vqa",
        "n_images": 1,
        "sensors": ["optical"],
    },
    {
        "image_paths": ["data/forest_fire.jpg"],
        "query": "Detect active fire spots in the image.",
        "expected_keywords": ["fire", "smoke", "burn", "active"],
        "task_type": "object_detection",
        "n_images": 1,
        "sensors": ["optical", "thermal"],
    },
    {
        "image_paths": ["data/deforestation_2020.tif", "data/deforestation_2025.tif"],
        "query": "Identify areas of deforestation between these two dates.",
        "expected_keywords": ["deforestation", "tree", "loss", "forest"],
        "task_type": "change_detection",
        "n_images": 2,
        "sensors": ["optical", "optical"],
    },
    {
        "image_paths": ["data/sample_optical.jpg"],
        "query": "Extract the road network from this image.",
        "expected_keywords": ["road", "network", "street", "highway"],
        "task_type": "segmentation",
        "n_images": 1,
        "sensors": ["optical"],
    },
    {
        "image_paths": ["data/sample_sar.tif"],
        "query": "What is the general topography of this region?",
        "expected_keywords": ["mountain", "flat", "hill", "valley", "terrain"],
        "task_type": "caption_image",
        "n_images": 1,
        "sensors": ["sar"],
    },
    {
        "image_paths": ["data/cloudy_image.jpg"],
        "query": "Classify the types of clouds present in the sky.",
        "expected_keywords": ["cloud", "cumulus", "cirrus", "stratus", "sky"],
        "task_type": "classification",
        "n_images": 1,
        "sensors": ["optical"],
    },
]

def get_test_cases() -> list[dict]:
    """Return the curated list of test cases.
    
    Note: For end-to-end evaluation, real images must be placed in 
    the data/ directory matching the paths in the test cases.
    """
    return TEST_CASES
