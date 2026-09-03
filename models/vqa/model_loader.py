"""
Singleton loader for Qwen2.5-VL-3B-Instruct model.

IMPORTANT: torch is imported lazily inside get_model_and_processor() so that
this module can be imported in CI/tests WITHOUT torch installed.
The mocked unit tests in tests/test_vqa.py patch get_model_and_processor
directly and never trigger the real import path.
"""
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

_model = None
_processor = None

def get_model_and_processor() -> Tuple:
    """
    Loads and returns the Qwen2.5-VL-3B-Instruct model and processor.
    Uses cached global instances if already loaded.
    """
    global _model, _processor
    
    if is_model_loaded():
        return _model, _processor

    logger.info("Loading Qwen2.5-VL-3B-Instruct model...")

    try:
        import torch
        from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    except ImportError as exc:
        logger.error("Required packages not installed: %s", exc)
        raise

    if torch.cuda.is_available():
        logger.info("GPU detected, loading model on GPU with bfloat16")
        _model = Qwen2VLForConditionalGeneration.from_pretrained(
            "Qwen/Qwen2.5-VL-3B-Instruct",
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
    else:
        logger.warning(
            "GPU not detected. Loading Qwen2.5-VL-3B-Instruct on CPU with float32. "
            "Inference will be slow — a working slow demo beats a broken fast one."
        )
        _model = Qwen2VLForConditionalGeneration.from_pretrained(
            "Qwen/Qwen2.5-VL-3B-Instruct",
            torch_dtype=torch.float32,
        )

    _processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-3B-Instruct")

    return _model, _processor


def is_model_loaded() -> bool:
    """Checks if the global model and processor are loaded."""
    return _model is not None and _processor is not None
