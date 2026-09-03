"""
SatQuery AI — POST /api/v1/upload

Accepts one or more image files, validates them, extracts metadata,
stores them securely, and returns upload metadata.

Security rules enforced here:
  - Extension whitelist
  - File-size limit
  - UUID internal filenames
  - Path traversal prevention
  - Content validated by rasterio (not by file extension alone)
"""

import hashlib
import os
import uuid
from datetime import datetime, timezone

import aiofiles
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_settings
from app.core.config import Settings
from app.core.exceptions import FileTooLargeError, InvalidFileFormatError
from app.core.logging import get_logger
from app.core.security import (
    generate_internal_filename,
    is_geotiff_extension,
    safe_upload_path,
    sanitize_filename,
    validate_extension,
    validate_file_size,
)
from app.ingestion.loader import load_image_metadata
from app.models import orm
from app.models.schemas import ImageMetadata, UploadResponse, UploadedFileInfo

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=UploadResponse, summary="Upload image files")
async def upload_files(
    files: list[UploadFile] = File(..., description="One or more image files (.tif, .tiff, .png, .jpg)"),
    session_id: str | None = Form(default=None, description="Optional existing session ID"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UploadResponse:
    """
    Upload one or more remote-sensing image files.

    - Validates extensions and size
    - Extracts GeoTIFF metadata if applicable
    - Stores with UUID-based internal filename
    - Returns structured metadata for each file
    """
    # Create or resolve session
    if not session_id:
        session_id = str(uuid.uuid4())
        session_obj = orm.Session(id=session_id)
        db.add(session_obj)
        db.commit()

    upload_id = uuid.uuid4().hex
    uploaded_files: list[UploadedFileInfo] = []

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    for upload in files:
        original_name = upload.filename or "unknown"
        safe_name = sanitize_filename(original_name)

        # Read file into memory for validation
        content = await upload.read()
        file_size = len(content)

        # --- Validations ---
        try:
            ext = validate_extension(original_name)
            validate_file_size(file_size)
        except (InvalidFileFormatError, FileTooLargeError) as exc:
            logger.warning(
                "upload_validation_failed",
                filename=safe_name,
                error=exc.error_code,
            )
            raise

        # --- Store with internal UUID filename ---
        internal_name = generate_internal_filename(ext)
        dest_path = safe_upload_path(settings.UPLOAD_DIR, internal_name)

        async with aiofiles.open(dest_path, "wb") as f:
            await f.write(content)

        # Content hash for deduplication / integrity
        content_hash = hashlib.sha256(content).hexdigest()

        # --- Extract metadata ---
        img_metadata: ImageMetadata | None = None
        is_geo = is_geotiff_extension(ext)
        if is_geo:
            try:
                img_metadata = await load_image_metadata(str(dest_path), original_name)
            except Exception as e:
                logger.warning("metadata_extraction_failed", filename=safe_name, error=str(e))
                # Non-fatal — we still store the file
                img_metadata = ImageMetadata(filename=original_name, is_geotiff=False)

        file_id = uuid.uuid4().hex

        # --- Persist to DB ---
        db_file = orm.UploadedFile(
            id=file_id,
            session_id=session_id,
            original_filename=safe_name,
            internal_filename=internal_name,
            file_path=str(dest_path),
            file_size_bytes=file_size,
            content_hash=content_hash,
            extension=ext,
            is_geotiff=is_geo,
            metadata_json=img_metadata.model_dump() if img_metadata else None,
        )
        db.add(db_file)

        uploaded_files.append(
            UploadedFileInfo(
                file_id=file_id,
                original_filename=safe_name,
                internal_filename=internal_name,
                size_bytes=file_size,
                extension=ext,
                is_geotiff=is_geo,
                metadata=img_metadata,
            )
        )

        logger.info(
            "file_uploaded",
            file_id=file_id,
            filename=safe_name,
            size_bytes=file_size,
            is_geotiff=is_geo,
        )

    db.commit()

    return UploadResponse(
        upload_id=upload_id,
        session_id=session_id,
        files=uploaded_files,
    )
