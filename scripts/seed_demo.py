"""
SatQuery AI — Seed Demo Script

Creates fixture data and sample requests for demonstration.
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.resolve()))

from app.core.config import get_settings
from app.models.database import SessionLocal, init_db
from app.models import orm

def seed():
    init_db()
    db = SessionLocal()
    try:
        session_id = "demo-session-001"
        existing = db.query(orm.Session).filter(orm.Session.id == session_id).first()
        if not existing:
            sess = orm.Session(id=session_id, client_info="Demo Seeder")
            db.add(sess)
            db.commit()
            print(f"✓ Seeded demo session: {session_id}")
        else:
            print(f"✓ Demo session already exists: {session_id}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
