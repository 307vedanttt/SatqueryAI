"""
SatQuery AI — Sessions route

GET /api/v1/session/{session_id}
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.models import orm
from app.models.schemas import SessionInfo

router = APIRouter()


@router.get("/session/{session_id}", response_model=SessionInfo, summary="Get session info")
async def get_session(session_id: str, db: Session = Depends(get_db)) -> SessionInfo:
    """Retrieve information about an existing session."""
    session = db.query(orm.Session).filter(orm.Session.id == session_id).first()
    if not session:
        raise NotFoundError(message=f"Session '{session_id}' not found.")

    analysis_count = db.query(orm.AnalysisRequest).filter(
        orm.AnalysisRequest.session_id == session_id
    ).count()
    upload_count = db.query(orm.UploadedFile).filter(
        orm.UploadedFile.session_id == session_id
    ).count()

    return SessionInfo(
        session_id=session.id,
        created_at=session.created_at,
        analysis_count=analysis_count,
        upload_count=upload_count,
    )
