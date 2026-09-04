"""
SatQuery AI — POST /api/imagery/validate & POST /api/imagery/upload

Endpoints for validating and uploading remote sensing imagery.
"""

import uuid
import os
import aiofiles
import hashlib
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
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
from app.ingestion.validation import validate_pair, ValidationResult, detect_sensor_configuration
from app.models import orm
from app.models.schemas import UploadResponse, UploadedFileInfo, ImageMetadata

router = APIRouter()
logger = get_logger(__name__)

async def process_upload(
    upload: UploadFile,
    settings: Settings,
    session_id: str
) -> tuple[UploadedFileInfo, ImageMetadata, bytes]:
    original_name = upload.filename or "unknown"
    safe_name = sanitize_filename(original_name)
    content = await upload.read()
    file_size = len(content)

    ext = validate_extension(original_name)
    validate_file_size(file_size)

    internal_name = generate_internal_filename(ext)
    dest_path = safe_upload_path(settings.UPLOAD_DIR, internal_name)

    async with aiofiles.open(dest_path, "wb") as f:
        await f.write(content)

    img_metadata = None
    is_geo = is_geotiff_extension(ext)
    if is_geo:
        try:
            img_metadata = await load_image_metadata(str(dest_path), original_name)
        except Exception as e:
            logger.warning("metadata_extraction_failed", filename=safe_name, error=str(e))
            img_metadata = ImageMetadata(filename=original_name, is_geotiff=False)
    else:
        img_metadata = await load_image_metadata(str(dest_path), original_name)

    file_id = uuid.uuid4().hex
    info = UploadedFileInfo(
        file_id=file_id,
        original_filename=safe_name,
        internal_filename=internal_name,
        size_bytes=file_size,
        extension=ext,
        is_geotiff=is_geo,
        metadata=img_metadata,
    )
    return info, img_metadata, content


@router.post("/validate", response_model=ValidationResult, summary="Validate image files")
async def validate_files(
    files: list[UploadFile] = File(..., description="One or two image files for validation"),
    configuration: str = Form(default="single", description="Expected configuration: 'single', 'optical_sar', 'bi_temporal'"),
    settings: Settings = Depends(get_settings),
) -> ValidationResult:
    """Validate uploaded remote-sensing imagery without persisting to DB."""
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")
    if len(files) > 2:
        raise HTTPException(status_code=400, detail="Maximum 2 files supported for validation")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    metadata_list = []
    errors = []
    
    for upload in files:
        try:
            _, meta, _ = await process_upload(upload, settings, "validation_session")
            metadata_list.append(meta)
        except Exception as e:
            errors.append(f"File {upload.filename}: {str(e)}")
            
    if errors:
        return ValidationResult(is_valid=False, errors=errors, metadata=metadata_list)

    sensor_type, confidence, source = "unknown", 0.0, "insufficient_metadata"
    pair_validation = None
    is_valid = True

    if len(metadata_list) == 1:
        if configuration != "single":
            errors.append(f"Expected {configuration} configuration, but received 1 file.")
            is_valid = False
        sensor_type, confidence, source = detect_sensor_configuration(metadata_list[0])
    
    elif len(metadata_list) == 2:
        if configuration == "single":
            errors.append("Expected single configuration, but received 2 files.")
            is_valid = False
        else:
            pair_validation = validate_pair(metadata_list[0], metadata_list[1], configuration)
            if not pair_validation.is_valid:
                is_valid = False

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        metadata=metadata_list,
        sensor_type=sensor_type,
        confidence=confidence,
        source=source,
        pair_validation=pair_validation
    )


@router.post("/upload", response_model=UploadResponse, summary="Upload and store image files")
async def upload_files(
    files: list[UploadFile] = File(..., description="One or more image files (.tif, .tiff, .png, .jpg)"),
    session_id: str | None = Form(default=None, description="Optional existing session ID"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UploadResponse:
    if not session_id:
        session_id = str(uuid.uuid4())
        session_obj = orm.Session(id=session_id)
        db.add(session_obj)
        db.commit()

    upload_id = uuid.uuid4().hex
    uploaded_files: list[UploadedFileInfo] = []
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    for upload in files:
        info, meta, content = await process_upload(upload, settings, session_id)
        content_hash = hashlib.sha256(content).hexdigest()
        
        db_file = orm.UploadedFile(
            id=info.file_id,
            session_id=session_id,
            original_filename=info.original_filename,
            internal_filename=info.internal_filename,
            file_path=str(safe_upload_path(settings.UPLOAD_DIR, info.internal_filename)),
            file_size_bytes=info.size_bytes,
            content_hash=content_hash,
            extension=info.extension,
            is_geotiff=info.is_geotiff,
            metadata_json=meta.model_dump() if meta else None,
        )
        db.add(db_file)
        uploaded_files.append(info)

    db.commit()

    return UploadResponse(
        upload_id=upload_id,
        session_id=session_id,
        files=uploaded_files,
    )

@router.get("/{image_id}", response_model=UploadedFileInfo, summary="Get image metadata")
async def get_image_info(
    image_id: str,
    db: Session = Depends(get_db)
) -> UploadedFileInfo:
    db_file = db.query(orm.UploadedFile).filter(orm.UploadedFile.id == image_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="Image not found")
        
    return UploadedFileInfo(
        file_id=db_file.id,
        original_filename=db_file.original_filename,
        internal_filename=db_file.internal_filename,
        size_bytes=db_file.file_size_bytes,
        extension=db_file.extension,
        is_geotiff=db_file.is_geotiff,
        metadata=ImageMetadata(**db_file.metadata_json) if db_file.metadata_json else None
    )
