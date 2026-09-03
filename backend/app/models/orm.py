"""
SatQuery AI — ORM Models

SQLAlchemy ORM table definitions.
Binary raster data is NEVER stored here — only paths and metadata.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    client_info: Mapped[str | None] = mapped_column(String(256), nullable=True)

    uploads: Mapped[list["UploadedFile"]] = relationship("UploadedFile", back_populates="session")
    analyses: Mapped[list["AnalysisRequest"]] = relationship("AnalysisRequest", back_populates="session")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sessions.id"), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(256))
    internal_filename: Mapped[str] = mapped_column(String(256), unique=True)
    file_path: Mapped[str] = mapped_column(String(512))
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extension: Mapped[str] = mapped_column(String(16))
    is_geotiff: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    session: Mapped["Session | None"] = relationship("Session", back_populates="uploads")


class AnalysisRequest(Base):
    __tablename__ = "analysis_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sessions.id"), nullable=True)
    query_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    input_configuration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    specialist_used: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    session: Mapped["Session | None"] = relationship("Session", back_populates="analyses")
    execution_steps: Mapped[list["ExecutionStepRecord"]] = relationship(
        "ExecutionStepRecord", back_populates="analysis_request"
    )


class ExecutionStepRecord(Base):
    __tablename__ = "execution_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_requests.id"))
    step_index: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(128))
    component: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    analysis_request: Mapped["AnalysisRequest"] = relationship(
        "AnalysisRequest", back_populates="execution_steps"
    )
