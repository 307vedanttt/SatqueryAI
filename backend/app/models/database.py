"""
SatQuery AI — Database Layer

SQLAlchemy setup with SQLite default.
The engine and session are abstracted here so PostgreSQL/PostGIS
can be substituted later by changing DATABASE_URL only.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def _get_engine():
    settings = get_settings()
    connect_args = {}
    if "sqlite" in settings.DATABASE_URL:
        connect_args = {"check_same_thread": False}
    return create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        echo=settings.DEBUG,
    )


engine = _get_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """Dependency: yield a DB session and close it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables on startup."""
    # Import ORM models so they register with Base.metadata
    from app.models import orm  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("database_initialized", url=get_settings().DATABASE_URL.split("///")[0])


def check_db_connection() -> bool:
    """Health check — return True if DB is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
