import numpy as np


def threshold_change_map(
    change_probability: np.ndarray,
    threshold: float = 0.3
) -> np.ndarray:
    """
    Convert probability map into a binary change map.

    Args:
        change_probability:
            Pixel-level probability map.

        threshold:
            Probability threshold.
            0.3 was selected using the validation set.

    Returns:
        Binary numpy array.
        1 = change
        0 = no change
    """

    return (
        change_probability >= threshold
    ).astype(np.uint8)


def calculate_change_percentage(
    change_probability: np.ndarray,
    threshold: float = 0.3
) -> float:
    """
    Calculate percentage of image pixels classified as changed.
    """

    binary_map = threshold_change_map(
        change_probability,
        threshold
    )

    total_pixels = binary_map.size

    if total_pixels == 0:
        return 0.0

    changed_pixels = np.sum(
        binary_map
    )

    percentage = (
        changed_pixels /
        total_pixels
    ) * 100.0

    return float(percentage)


def calculate_change_confidence(
    change_probability: np.ndarray,
    threshold: float = 0.3
) -> float:
    """
    Estimate confidence from the predicted changed pixels.

    This is NOT the model's calibrated probability of the
    complete prediction. It is the mean predicted probability
    among pixels classified as changed.
    """

    changed_pixels = change_probability[
        change_probability >= threshold
    ]

    if changed_pixels.size == 0:
        return 0.0

    confidence = np.mean(
        changed_pixels
    )

    return float(confidence)


def calculate_mean_change_probability(
    change_probability: np.ndarray
) -> float:
    """
    Calculate the mean change probability across the image.
    """

    if change_probability.size == 0:
        return 0.0

    return float(
        np.mean(change_probability)
    )


def calculate_change_statistics(
    change_probability: np.ndarray,
    threshold: float = 0.3
) -> dict:
    """
    Calculate useful change statistics.
    """

    binary_map = threshold_change_map(
        change_probability,
        threshold
    )

    changed_pixels = int(
        np.sum(binary_map)
    )

    total_pixels = int(
        binary_map.size
    )

    change_percentage = (
        changed_pixels /
        total_pixels *
        100.0
        if total_pixels > 0
        else 0.0
    )

    changed_confidence = (
        float(
            np.mean(
                change_probability[
                    binary_map == 1
                ]
            )
        )
        if changed_pixels > 0
        else 0.0
    )

    return {
        "threshold": float(threshold),
        "total_pixels": total_pixels,
        "changed_pixels": changed_pixels,
        "change_percentage": float(
            change_percentage
        ),
        "mean_change_probability": float(
            np.mean(change_probability)
        ),
        "changed_pixel_confidence": changed_confidence,
        "max_change_probability": float(
            np.max(change_probability)
        ),
    }