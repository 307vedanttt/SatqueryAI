# Data Directory

This directory is used to store sample satellite imagery and geospatial data for local testing, evaluation, and demonstrations of SatQuery AI.

## Supported Formats
- **Optical/VHR:** `.jpg`, `.png`, `.tif`
- **SAR/Multispectral/Hyperspectral:** Multi-band GeoTIFFs (`.tif`)

## Usage in Evaluation
The `evaluation/test_set.py` script references images in this folder (e.g., `data/sample_optical.jpg`). To run end-to-end evaluations without skipping test cases, place corresponding sample files here. You can use placeholder images for basic pipeline testing.

*Note: Large datasets should NOT be committed to the repository. Please use `.gitignore` to exclude large `.tif` files and only commit small sample `.jpg` files if necessary.*
