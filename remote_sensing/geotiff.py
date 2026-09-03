"""
remote_sensing/geotiff.py — GeoTIFF and benchmark image loading

TWO LOADING PATHS (keep these distinct in your mental model):

OPERATIONAL PATH: load_geotiff()
    For real satellite data in GeoTIFF format.
    Uses rasterio to extract genuine CRS, resolution, and band metadata.
    Returns crs="none" (sentinel string) ONLY if the file itself has no CRS.
    All downstream processing (change detection, optical-SAR fusion) should
    prefer this path for real mission data.

BENCHMARK PATH: load_benchmark_image()
    For PNG/JPEG benchmark datasets (VRSBench, RSVQA, DOTA, etc.) that
    lack geospatial metadata entirely.
    Sets crs="none", resolution_m=0.0 — intentionally, because these images
    have no real-world coordinate system.
    check_coregistration() will correctly reject "none" CRS pairs before
    attempting fusion or change detection.

SENTINEL CONVENTION
-------------------
crs="none" is the project-wide sentinel meaning "no geospatial reference".
It is a lowercase string, not Python None. This makes it safe to store in
SQLite text columns and easy to test with a simple string comparison.
"""

import logging
import os
import re
from typing import Optional

import numpy as np
from PIL import Image

from schemas.contracts import ImageMetadata

logger = logging.getLogger(__name__)

# String sentinel for "no CRS available"
_NO_CRS: str = "none"

# SAR filename hints — case-insensitive
_SAR_HINTS: tuple[str, ...] = ("sar", "s1_", "sentinel-1", "sentinel1", "slc", "grd")


class ImageLoadError(Exception):
    """
    Raised when an image cannot be loaded from disk.

    Wraps raw library exceptions (rasterio.errors.RasterioIOError, PIL IOError,
    FileNotFoundError) with a human-readable message that includes the file path
    so the caller can surface it directly to the user without chasing stack traces.
    """


def _detect_sensor_from_path(path: str) -> str:
    """
    Heuristically detect sensor type from filename hints.

    Checks lowercase path for SAR-indicating substrings. Returns "sar" if any
    hint matches, "optical" otherwise. This is a best-effort guess — calling
    code should always prefer sensor_override when the sensor is known.

    Args:
        path: File path to inspect.

    Returns:
        "sar" or "optical".
    """
    lower = path.lower()
    for hint in _SAR_HINTS:
        if hint in lower:
            logger.debug("SAR hint '%s' detected in path '%s'", hint, path)
            return "sar"
    return "optical"


def load_geotiff(
    path: str,
    sensor_override: Optional[str] = None,
) -> tuple[np.ndarray, ImageMetadata]:
    """
    Load a GeoTIFF and return pixel data + structured metadata.

    OPERATIONAL PATH — for real satellite imagery with geospatial metadata.

    Args:
        path: Absolute or relative path to the GeoTIFF file.
        sensor_override: If provided, use this sensor string instead of the
                         heuristic detection. Pass "optical" or "sar" explicitly
                         when you know the sensor type.

    Returns:
        Tuple of:
            - np.ndarray of shape (bands, height, width)
            - ImageMetadata with all fields populated from the file's metadata

    Raises:
        ImageLoadError: If the file cannot be opened or read. The message includes
                        the file path and the underlying library error.
    """
    import rasterio  # lazy import — rasterio is optional for benchmark-only usage

    logger.info("load_geotiff: opening '%s'", path)

    try:
        with rasterio.open(path) as dataset:
            # CRS — use sentinel string if file has no CRS
            if dataset.crs is not None:
                crs = dataset.crs.to_string()
            else:
                crs = _NO_CRS
                logger.warning(
                    "GeoTIFF '%s' has no CRS — setting crs='%s'. "
                    "This file cannot be used in co-registration checks.",
                    path, _NO_CRS,
                )

            width = dataset.width
            height = dataset.height
            bands = dataset.count

            # Resolution: average of x/y pixel size (may differ for non-square pixels)
            res_x, res_y = dataset.res
            resolution_m = (res_x + res_y) / 2.0

            # Pixel data: shape (bands, height, width)
            data = dataset.read()

            # Sensor detection
            sensor = sensor_override or _detect_sensor_from_path(path)

            # Acquisition date — try common TIFF tags, else None
            tags = dataset.tags()
            acquisition_date = (
                tags.get("TIFFTAG_DATETIME")
                or tags.get("acquisition_date")
                or tags.get("DATE_ACQUIRED")
                or None
            )

        meta = ImageMetadata(
            sensor=sensor,
            crs=crs,
            width=width,
            height=height,
            bands=bands,
            resolution_m=resolution_m,
            acquisition_date=acquisition_date,
            file_path=path,
        )
        logger.info(
            "load_geotiff: loaded %s — %dx%d, %d band(s), CRS=%s, %.1fm resolution",
            sensor, width, height, bands, crs, resolution_m,
        )
        return data, meta

    except FileNotFoundError as exc:
        raise ImageLoadError(
            f"GeoTIFF not found: '{path}'. "
            "Check that the file path is correct and the file exists."
        ) from exc
    except Exception as exc:
        # Catch rasterio.errors.RasterioIOError and any other library exception
        raise ImageLoadError(
            f"Failed to read GeoTIFF '{path}': {type(exc).__name__}: {exc}. "
            "Ensure the file is a valid GeoTIFF and not corrupted."
        ) from exc


def load_benchmark_image(
    path: str,
    sensor: str,
) -> tuple[np.ndarray, ImageMetadata]:
    """
    Load a PNG/JPEG benchmark image and return pixel data + minimal metadata.

    BENCHMARK PATH — for images from VRSBench, RSVQA, DOTA, and similar datasets
    that are standard image files (not GeoTIFFs) and have NO geospatial reference.

    Key differences from load_geotiff():
      - crs is set to the sentinel string "none" (NOT a real CRS string)
      - resolution_m is 0.0 (no real-world ground sampling distance known)
      - No acquisition_date (typically unknown for benchmark datasets)

    These intentional placeholder values mean check_coregistration() will
    CORRECTLY reject any pair that includes a benchmark image — you cannot
    co-register an image that has no coordinate system.

    Args:
        path: Absolute or relative path to the PNG, JPEG, or other PIL-readable file.
        sensor: Sensor type string ("optical", "sar", or "multispectral"). Caller
                must specify this explicitly since it cannot be auto-detected from
                benchmark data.

    Returns:
        Tuple of:
            - np.ndarray of shape (bands, height, width), dtype uint8
            - ImageMetadata with crs="none" and resolution_m=0.0

    Raises:
        ImageLoadError: If the file cannot be opened or is not a valid image.
    """
    logger.info("load_benchmark_image: opening '%s' (sensor=%s)", path, sensor)

    try:
        img = Image.open(path)
        data = np.array(img)

        if data.ndim == 2:
            # Grayscale image — reshape to (1, H, W)
            data = data.reshape(1, data.shape[0], data.shape[1])
        elif data.ndim == 3:
            # (H, W, C) → (C, H, W)
            data = data.transpose(2, 0, 1)
        else:
            raise ImageLoadError(
                f"Unexpected array shape {data.shape} for image '{path}'. "
                "Expected 2D (grayscale) or 3D (H×W×C) array."
            )

        _, height, width = data.shape
        bands = data.shape[0]

        # Benchmark data: crs="none" and resolution_m=0.0 are intentional.
        # Do NOT change these to real values — their role is to signal to
        # check_coregistration() that this image cannot be spatially referenced.
        meta = ImageMetadata(
            sensor=sensor,
            crs=_NO_CRS,        # sentinel — this image has no real CRS
            width=width,
            height=height,
            bands=bands,
            resolution_m=0.0,   # unknown ground sampling distance
            acquisition_date=None,
            file_path=path,
        )
        logger.info(
            "load_benchmark_image: loaded %s — %dx%d, %d band(s) [no geospatial ref]",
            sensor, width, height, bands,
        )
        return data, meta

    except ImageLoadError:
        raise
    except FileNotFoundError as exc:
        raise ImageLoadError(
            f"Benchmark image not found: '{path}'. "
            "Check that the file path is correct and the file exists."
        ) from exc
    except Exception as exc:
        raise ImageLoadError(
            f"Failed to read benchmark image '{path}': {type(exc).__name__}: {exc}. "
            "Ensure the file is a valid PNG, JPEG, or PIL-compatible image."
        ) from exc
