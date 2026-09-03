"""
SatQuery AI — Ingestion: Raster Metadata Extraction

Uses rasterio to extract comprehensive GeoTIFF metadata.
All metadata fields that cannot be determined are set to None — never fabricated.

This module is synchronous (rasterio is blocking I/O).
Always call via asyncio.run_in_executor() in async context.
"""

import uuid
from pathlib import Path
from typing import Any

from app.core.exceptions import CorruptedRasterError, InvalidCRSError
from app.core.logging import get_logger
from app.models.schemas import ImageMetadata

logger = get_logger(__name__)

# Attempt to import rasterio — fail gracefully so unit tests without GDAL still work
try:
    import rasterio
    from rasterio.crs import CRS
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    logger.warning("rasterio_not_available", message="rasterio not installed. GeoTIFF support limited.")


def extract_raster_metadata(file_path: str, original_filename: str) -> ImageMetadata:
    """
    Open a raster file with rasterio and extract structured metadata.
    
    Raises:
        CorruptedRasterError: If the file cannot be opened or read.
        ImportError: If rasterio is not available (should be caught by caller).
    """
    if not RASTERIO_AVAILABLE:
        raise ImportError(
            "rasterio is not installed. Install it with: pip install rasterio"
        )

    try:
        with rasterio.open(file_path) as src:
            # CRS
            crs_string: str | None = None
            if src.crs:
                try:
                    crs_string = src.crs.to_epsg()
                    crs_string = f"EPSG:{crs_string}" if crs_string else src.crs.to_string()
                except Exception:
                    crs_string = str(src.crs) if src.crs else None

            # Resolution — pixel size in CRS units
            resolution: tuple[float, float] | None = None
            if src.transform:
                try:
                    res = src.res
                    resolution = (float(res[0]), float(res[1]))
                except Exception:
                    resolution = None

            # Bounds
            bounds: tuple[float, float, float, float] | None = None
            try:
                b = src.bounds
                bounds = (b.left, b.bottom, b.right, b.top)
            except Exception:
                bounds = None

            # Nodata
            nodata: float | None = None
            try:
                nd = src.nodata
                nodata = float(nd) if nd is not None else None
            except Exception:
                nodata = None

            # Tag-based metadata
            raw_tags: dict[str, Any] = {}
            try:
                raw_tags = dict(src.tags())
            except Exception:
                pass

            # Try to infer sensor/date from tags
            sensor: str | None = _extract_tag(raw_tags, ["SENSOR", "Sensor", "sensor", "SPACECRAFT_ID"])
            acq_date: str | None = _extract_tag(
                raw_tags,
                ["ACQUISITION_DATE", "DATE_ACQUIRED", "Acquisition_date", "acquisition_datetime"],
            )

            # Classify image type from band count heuristic
            image_type = _classify_image_type(src.count, src.dtypes, raw_tags)

            return ImageMetadata(
                image_id=uuid.uuid4().hex,
                filename=original_filename,
                width=src.width,
                height=src.height,
                bands=src.count,
                dtype=str(src.dtypes[0]) if src.dtypes else None,
                crs=crs_string,
                resolution=resolution,
                bounds=bounds,
                nodata=nodata,
                driver=src.driver,
                is_geotiff=True,
                sensor=sensor,
                acquisition_date=acq_date,
                image_type=image_type,
                raw_metadata=raw_tags,
            )

    except (CorruptedRasterError, ImportError):
        raise
    except Exception as exc:
        logger.error("raster_open_failed", file=file_path, error=str(exc))
        raise CorruptedRasterError(
            message=f"The file '{Path(file_path).name}' could not be read as a valid raster."
        )


def _extract_tag(tags: dict[str, Any], keys: list[str]) -> str | None:
    """Try multiple possible tag key names, return first match."""
    for key in keys:
        value = tags.get(key)
        if value:
            return str(value)
    return None


def _classify_image_type(band_count: int, dtypes: tuple, tags: dict[str, Any]) -> str:
    """
    Heuristic image type classification.
    Returns: 'optical' | 'sar' | 'multispectral' | 'hyperspectral' | 'unknown'
    
    This is a best-effort heuristic. Actual classification should use sensor metadata.
    """
    # Check tags first
    sensor = _extract_tag(tags, ["SENSOR", "sensor", "SPACECRAFT_ID", "MISSION"])
    if sensor:
        sensor_lower = sensor.lower()
        if any(s in sensor_lower for s in ["sentinel-1", "ers", "palsar", "radarsat", "sar"]):
            return "sar"
        if any(s in sensor_lower for s in ["sentinel-2", "landsat", "modis", "worldview"]):
            return "multispectral"

    # Fall back to band count heuristic
    if band_count == 1:
        # Could be SAR, panchromatic, or single-band raster
        dtype_str = str(dtypes[0]) if dtypes else ""
        if "complex" in dtype_str or "float" in dtype_str:
            return "sar"  # SAR intensity or complex data
        return "optical"
    elif band_count == 3:
        return "optical"
    elif 4 <= band_count <= 12:
        return "multispectral"
    elif band_count > 12:
        return "hyperspectral"
    else:
        return "unknown"
