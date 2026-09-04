"""
SatQuery AI - Change Detection Module

Provides:
- Siamese ResNet50 change detection
- Change probability map generation
- Change percentage calculation
- Change detection specialist interface
"""

from .encoder import ChangeDetectionModel, preprocess_image
from .difference import (
    calculate_change_percentage,
    calculate_change_confidence,
)
from .change_map import (
    save_change_map,
    save_change_overlay,
)

__all__ = [
    "ChangeDetectionModel",
    "preprocess_image",
    "calculate_change_percentage",
    "calculate_change_confidence",
    "save_change_map",
    "save_change_overlay",
]