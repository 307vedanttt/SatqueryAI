"""
SatQuery AI — Ingestion: Loader

Orchestrates loading and metadata extraction for uploaded files.
Dispatches to raster.py for GeoTIFF, or provides basic metadata for standard images.
"""

import asyncio
from pathlib import Path

from app.core.logging import get_logger
from app.core.security import is_geotiff_extension
from app.ingestion.raster import extract_raster_metadata
from app.models.schemas import ImageMetadata

logger = get_logger(__name__)


async def load_image_metadata(file_path: str, original_filename: str) -> ImageMetadata:
    """
    Load and extract metadata from an uploaded image file.
    
    For GeoTIFF: full rasterio-based extraction.
    For standard images (PNG/JPEG): basic metadata via Pillow.
    
    This runs the synchronous rasterio extraction in a thread pool
    to avoid blocking the async event loop.
    """
    ext = Path(file_path).suffix.lower()

    if is_geotiff_extension(ext):
        # Run sync rasterio extraction in thread pool
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(
            None,
            extract_raster_metadata,
            file_path,
            original_filename,
        )
        return metadata
    else:
        # Standard image — extract basic dimensions via Pillow
        return await _extract_standard_image_metadata(file_path, original_filename)


async def _extract_standard_image_metadata(file_path: str, original_filename: str) -> ImageMetadata:
    """Extract basic metadata from PNG/JPEG using Pillow."""
    try:
        from PIL import Image
        loop = asyncio.get_event_loop()

        def _read():
            with Image.open(file_path) as img:
                return img.size, img.mode

        size, mode = await loop.run_in_executor(None, _read)
        width, height = size
        bands = len(mode)  # e.g. RGB=3, RGBA=4, L=1

        return ImageMetadata(
            filename=original_filename,
            width=width,
            height=height,
            bands=bands,
            dtype="uint8",
            crs=None,
            resolution=None,
            bounds=None,
            is_geotiff=False,
            image_type="optical",
        )
    except Exception as e:
        logger.warning("pillow_metadata_failed", file=file_path, error=str(e))
        return ImageMetadata(filename=original_filename, is_geotiff=False)
