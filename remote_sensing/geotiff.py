"""
SatQuery AI — GeoTIFF & Remote Sensing Ingestion Engine (Person D - Part 1)

Handles GeoTIFF metadata extraction via rasterio and benchmark image fallback (PNG/JPEG).
Extracts:
  - Pixel array
  - CRS string (e.g. 'EPSG:4326')
  - Spatial resolution in meters
  - Bounding dimensions (width, height, bands)
  - Sensor classification heuristic ('optical' vs 'sar')
"""

import logging
from typing import Tuple, Optional
import numpy as np
from PIL import Image

from schemas.contracts import ImageMetadata

logger = logging.getLogger("satquery.remote_sensing.geotiff")


class ImageLoadError(Exception):
    """Custom exception raised when an image file fails to load."""
    pass


def load_geotiff(path: str, sensor_override: Optional[str] = None) -> Tuple[np.ndarray, ImageMetadata]:
    """
    Load GeoTIFF file using rasterio.
    Returns (pixel_array, ImageMetadata).
    
    Raises:
        ImageLoadError: If file cannot be read or rasterio is missing.
    """
    try:
        import rasterio
    except ImportError:
        logger.warning("rasterio library not installed. Falling back to PIL load.")
        raise ImageLoadError("rasterio library is not installed. Install with: pip install rasterio")

    try:
        with rasterio.open(path) as src:
            data = src.read()  # [bands, height, width]

            # Determine CRS string
            crs_str = "EPSG:4326"
            if src.crs:
                try:
                    epsg = src.crs.to_epsg()
                    crs_str = f"EPSG:{epsg}" if epsg else src.crs.to_string()
                except Exception:
                    crs_str = str(src.crs)

            # Spatial resolution in meters
            resolution_m = 10.0
            if src.transform:
                try:
                    res = src.res
                    resolution_m = float(res[0])
                except Exception:
                    pass

            # Sensor detection heuristic
            path_lower = path.lower()
            if sensor_override:
                sensor = sensor_override.lower()
            elif any(s in path_lower for s in ["sar", "s1", "sentinel-1", "radarsat", "palsar"]):
                sensor = "sar"
            else:
                sensor = "optical"

            meta = ImageMetadata(
                sensor=sensor,
                crs=crs_str,
                width=src.width,
                height=src.height,
                bands=src.count,
                resolution_m=resolution_m,
                file_path=path,
            )

            logger.info(f"Loaded GeoTIFF '{path}': {meta.width}x{meta.height}px, {meta.sensor.upper()}, CRS={meta.crs}")
            return data, meta

    except Exception as e:
        logger.error(f"Failed to load GeoTIFF from '{path}': {e}")
        raise ImageLoadError(f"Failed to load GeoTIFF from '{path}': {e}")


def load_benchmark_image(path: str, sensor: str = "optical") -> Tuple[np.ndarray, ImageMetadata]:
    """
    Fallback loader for benchmark images (PNG/JPEG from VRSBench, RSVQA, etc.).
    These lack spatial CRS data -> crs="none", resolution_m=0.0.
    """
    try:
        with Image.open(path) as img:
            img_rgb = img.convert("RGB")
            data = np.array(img_rgb)
            width, height = img.size
            bands = 3

            meta = ImageMetadata(
                sensor=sensor,
                crs="none",
                width=width,
                height=height,
                bands=bands,
                resolution_m=0.0,
                file_path=path,
            )

            logger.info(f"Loaded benchmark image '{path}': {width}x{height}px (No CRS)")
            return data, meta
    except Exception as e:
        logger.error(f"Failed to load benchmark image from '{path}': {e}")
        raise ImageLoadError(f"Failed to load benchmark image from '{path}': {e}")
