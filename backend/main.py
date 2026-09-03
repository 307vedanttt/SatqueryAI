"""
backend/main.py — FastAPI Backend for SatQuery AI

Exposes the agent core (Executor) via HTTP, logging every request
to a local SQLite database for auditability.
"""
import os
import tempfile
import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import asynccontextmanager

from agent.executor import Executor
from agent.trace import format_trace_as_dict
from remote_sensing.geotiff import load_benchmark_image
from schemas.contracts import ImageMetadata, SpecialistRequest

# --- Database Setup (SQLAlchemy) ---
DATABASE_URL = "sqlite:///./satquery_logs.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    query_text = Column(Text, nullable=False)
    task_classified = Column(String, nullable=True)
    confidence_tier = Column(String, nullable=True)
    answer_text = Column(Text, nullable=True)
    status = Column(String, nullable=False)

# Initialize executor
executor = Executor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown

app = FastAPI(title="SatQuery AI API", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryResponse(BaseModel):
    status: str
    task: str
    confidence_tier: str
    answer: str
    error_message: Optional[str] = None
    trace: list

@app.get("/health")
def health_check():
    return {"status": "ok"}

def _guess_sensor(filename: str) -> str:
    lower = filename.lower()
    if any(hint in lower for hint in ("sar", "s1_", "sentinel-1", "sentinel1")):
        return "sar"
    return "optical"

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(
    query: str = Form(...),
    images: List[UploadFile] = File(...),
):
    if not images:
        raise HTTPException(status_code=400, detail="At least one image is required.")

    # Save uploaded files temporarily to process them
    temp_files = []
    meta_list = []
    try:
        for img in images:
            suffix = os.path.splitext(img.filename)[1] if img.filename else ""
            fd, path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            with open(path, "wb") as f:
                f.write(await img.read())
            temp_files.append(path)
            
            # Load metadata (using benchmark loader for arbitrary uploads without real geospatial metadata)
            sensor = _guess_sensor(img.filename or "")
            _, meta = load_benchmark_image(path, sensor)
            meta_list.append(meta)

        request = SpecialistRequest(query=query, images=meta_list)
        response, trace = executor.run(request)

        # Log to SQLite
        db = SessionLocal()
        try:
            log_entry = QueryLog(
                query_text=query,
                task_classified=response.task,
                confidence_tier=response.confidence_tier,
                answer_text=response.answer,
                status=response.status
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            print(f"Error logging to DB: {e}")
        finally:
            db.close()

        return QueryResponse(
            status=response.status,
            task=response.task,
            confidence_tier=response.confidence_tier,
            answer=response.answer if response.status == "success" else "",
            error_message=response.error_message,
            trace=format_trace_as_dict(trace)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp files
        for path in temp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
