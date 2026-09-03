"""
SatQuery AI — Model Loader (Person B)

Singleton model loader for Qwen2.5-VL-3B-Instruct.
Loads model into GPU (if available) or CPU float32 fallback ONCE per process.
"""

import logging
import torch
from typing import Tuple, Any, Optional

logger = logging.getLogger("satquery.models.vqa.model_loader")

_MODEL_ID = "Qwen/Qwen2.5-VL-3B-Instruct"
_CACHED_MODEL: Optional[Any] = None
_CACHED_PROCESSOR: Optional[Any] = None


def is_model_loaded() -> bool:
    """Return True if model and processor are cached in memory."""
    return _CACHED_MODEL is not None and _CACHED_PROCESSOR is not None


def get_model_and_processor() -> Tuple[Any, Any]:
    """
    Get or load Qwen2.5-VL-3B-Instruct singleton.
    
    GPU: bfloat16 / float16 with device_map="auto"
    CPU: float32 fallback with clear logging
    """
    global _CACHED_MODEL, _CACHED_PROCESSOR

    if is_model_loaded():
        return _CACHED_MODEL, _CACHED_PROCESSOR

    logger.info(f"Loading singleton model: {_MODEL_ID}")

    try:
        from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

        has_gpu = torch.cuda.is_available()
        if has_gpu:
            logger.info("GPU detected — loading Qwen2.5-VL with float16 / device_map='auto'")
            model = Qwen2VLForConditionalGeneration.from_pretrained(
                _MODEL_ID,
                torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
                device_map="auto",
            )
        else:
            logger.warning("No GPU detected — loading Qwen2.5-VL on CPU in float32 (inference will be slow)")
            model = Qwen2VLForConditionalGeneration.from_pretrained(
                _MODEL_ID,
                torch_dtype=torch.float32,
                device_map="cpu",
            )

        processor = AutoProcessor.from_pretrained(_MODEL_ID)

        _CACHED_MODEL = model
        _CACHED_PROCESSOR = processor

        logger.info(f"Successfully loaded and cached {_MODEL_ID}")
        return _CACHED_MODEL, _CACHED_PROCESSOR

    except Exception as e:
        logger.error(f"Failed to load {_MODEL_ID}: {e}")
        raise RuntimeError(f"Model load error for {_MODEL_ID}: {e}")
