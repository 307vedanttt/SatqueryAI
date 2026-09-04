from pathlib import Path

import numpy as np
from PIL import Image


def save_change_map(
    change_probability: np.ndarray,
    output_path: str,
    threshold: float = 0.3
) -> str:
    """
    Save binary change map.

    Black  = no change
    White  = change
    """

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    binary_map = (
        change_probability >= threshold
    ).astype(np.uint8) * 255

    image = Image.fromarray(
        binary_map,
        mode="L"
    )

    image.save(
        output_path
    )

    return str(output_path)


def save_probability_map(
    change_probability: np.ndarray,
    output_path: str
) -> str:
    """
    Save the raw probability map as a grayscale image.

    Black  = low change probability
    White  = high change probability
    """

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    probability_uint8 = (
        np.clip(
            change_probability,
            0.0,
            1.0
        ) * 255
    ).astype(np.uint8)

    image = Image.fromarray(
        probability_uint8,
        mode="L"
    )

    image.save(
        output_path
    )

    return str(output_path)


def save_change_overlay(
    original_image_path: str,
    change_probability: np.ndarray,
    output_path: str,
    threshold: float = 0.3,
    alpha: float = 0.5
) -> str:
    """
    Create an overlay showing detected changes
    on top of the original satellite image.

    Changed pixels are highlighted in red.
    """

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    original = Image.open(
        original_image_path
    ).convert("RGB")

    original = original.resize(
        (
            change_probability.shape[1],
            change_probability.shape[0]
        ),
        Image.Resampling.BILINEAR
    )

    original_array = np.asarray(
        original,
        dtype=np.float32
    )

    binary_map = (
        change_probability >= threshold
    )

    overlay = original_array.copy()

    # Red overlay for changed pixels
    red = np.zeros_like(
        original_array
    )

    red[:, :, 0] = 255.0

    mask = binary_map[:, :, np.newaxis]

    overlay = np.where(
        mask,
        (
            (1.0 - alpha) *
            original_array
            +
            alpha *
            red
        ),
        original_array
    )

    overlay = np.clip(
        overlay,
        0,
        255
    ).astype(np.uint8)

    result = Image.fromarray(
        overlay,
        mode="RGB"
    )

    result.save(
        output_path
    )

    return str(output_path)