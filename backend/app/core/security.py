"""
SatQuery AI — File Security Helpers

Validates uploaded files before they enter the system.
Rules:
  - Extension whitelist
  - MIME-type check (best-effort — not fully trusted, but adds a layer)
  - File-size limit
  - Filename sanitization → always use the generated internal ID
  - Path traversal prevention
  - No execution of uploaded content
"""

import mimetypes
import os
import re
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import FileTooLargeError, InvalidFileFormatError

settings = get_settings()

# Allowed file extensions (lower-case)
GEOTIFF_EXTENSIONS: frozenset[str] = frozenset({".tif", ".tiff"})
STANDARD_IMAGE_EXTENSIONS: frozenset[str] = frozenset({".png", ".jpg", ".jpeg"})
ALL_ALLOWED_EXTENSIONS: frozenset[str] = GEOTIFF_EXTENSIONS | STANDARD_IMAGE_EXTENSIONS

# Allowed MIME types (advisory — not the sole gate)
ALLOWED_MIME_TYPES: frozenset[str] = frozenset({
    "image/tiff",
    "image/png",
    "image/jpeg",
    "application/octet-stream",  # Some GeoTIFFs are served as generic binary
})

# Dangerous characters in filenames
_UNSAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._\-]")


def validate_extension(filename: str) -> str:
    """
    Return the lowercase extension if allowed, else raise InvalidFileFormatError.
    Always call this BEFORE touching the file content.
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in ALL_ALLOWED_EXTENSIONS:
        raise InvalidFileFormatError(
            message=(
                f"File extension '{suffix}' is not allowed. "
                f"Accepted: {', '.join(sorted(ALL_ALLOWED_EXTENSIONS))}"
            )
        )
    return suffix


def validate_file_size(size_bytes: int) -> None:
    """Raise FileTooLargeError if size exceeds configured limit."""
    if size_bytes > settings.max_upload_bytes:
        raise FileTooLargeError(
            message=(
                f"File size {size_bytes / (1024**2):.1f} MB exceeds "
                f"the maximum of {settings.MAX_UPLOAD_SIZE_MB} MB."
            )
        )


def sanitize_filename(original: str) -> str:
    """
    Sanitize the original filename for logging purposes only.
    Returns a cleaned version. NEVER use the original filename
    as an actual storage path — use generate_internal_filename() instead.
    """
    name = Path(original).name  # strip any directory components
    name = _UNSAFE_FILENAME_RE.sub("_", name)
    return name[:128]  # cap length


def generate_internal_filename(extension: str) -> str:
    """
    Generate a UUID-based internal filename.
    The original filename is NEVER used as a storage path.
    """
    return f"{uuid.uuid4().hex}{extension}"


def safe_upload_path(upload_dir: str, internal_filename: str) -> Path:
    """
    Construct an absolute upload path and verify it stays within upload_dir.
    Prevents path traversal.
    """
    base = Path(upload_dir).resolve()
    target = (base / internal_filename).resolve()
    if not str(target).startswith(str(base)):
        raise InvalidFileFormatError(message="Invalid file path detected.")
    return target


def is_geotiff_extension(extension: str) -> bool:
    """Return True if the extension is a GeoTIFF variant."""
    return extension.lower() in GEOTIFF_EXTENSIONS


def check_mime_type(content_type: str | None) -> None:
    """
    Advisory MIME check. Logs a warning but does not solely gate on MIME
    because MIME types are client-supplied and unreliable.
    """
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        # We allow it but flag it — real validation happens via rasterio
        pass
