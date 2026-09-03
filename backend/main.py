"""
SatQuery AI — FastAPI Query Endpoint with SQLite QueryLog (Person E - Priority 2)
"""

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from schemas.contracts import ImageMetadata, SpecialistRequest
from agent.executor import Executor
from agent.trace import format_trace_as_dict

# SQLite DB Setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./satquery_logs.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    query_text = Column(Text, nullable=False)
    task_classified = Column(String(64))
    confidence_tier = Column(String(32))
    answer_text = Column(Text)
    status = Column(String(32))


Base.metadata.create_all(bind=engine)

app = FastAPI(title="SatQuery AI Backend Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = Executor()


@app.get("/health")
async def health():
    return {"status": "ok", "app": "SatQuery AI SIH26167 API"}


@app.post("/query")
async def query_endpoint(
    query: str = Form(...),
    files: list[UploadFile] = File(...),
):
    upload_dir = "./data/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    images_meta = []
    for f in files:
        file_path = os.path.join(upload_dir, f.filename)
        content = await f.read()
        with open(file_path, "wb") as out:
            out.write(content)

        # Simple sensor detection heuristic
        sensor = "sar" if "sar" in f.filename.lower() or "s1" in f.filename.lower() else "optical"
        images_meta.append(
            ImageMetadata(
                sensor=sensor,
                crs="EPSG:4326",
                width=1024,
                height=1024,
                resolution_m=10.0,
                file_path=file_path,
            )
        )

    req = SpecialistRequest(query=query, images=images_meta)
    resp, trace = executor.run(req)

    # Log to SQLite
    db = SessionLocal()
    try:
        log_entry = QueryLog(
            query_text=query,
            task_classified=resp.task,
            confidence_tier=resp.confidence_tier,
            answer_text=resp.answer,
            status=resp.status,
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

    return {
        "response": resp.model_dump(mode="json"),
        "trace": format_trace_as_dict(trace),
    }
