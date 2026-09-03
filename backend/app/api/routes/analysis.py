"""
SatQuery AI — Analysis Route

POST /api/v1/analyze         — Run full analysis pipeline
GET  /api/v1/analysis/{id}   — Retrieve stored result
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_registry, get_settings
from app.core.config import Settings
from app.core.exceptions import InsufficientEvidenceError, NotFoundError
from app.core.logging import get_logger
from app.models import orm
from app.models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatus,
    AnswerBlock,
    ConfidenceBreakdown,
    ConfidenceLabel,
    DisagreementResult,
    ExecutionStep,
    ExecutionStepStatus,
    ImageMetadata,
    InputConfiguration,
    IntentResult,
    QueryIntent,
    SpecialistRequest,
)
from app.registry.registry import SpecialistRegistry
from app.router.classifier import classify_input_configuration
from app.router.execution_graph import ExecutionGraph
from app.router.planner import classify_intent
from app.evidence.confidence import ConfidenceCalculator
from app.evidence.disagreement import DisagreementDetector
from app.evidence.synthesizer import EvidenceSynthesizer
from app.trace.execution import TraceRecorder

router = APIRouter()
logger = get_logger(__name__)


@router.post("/analyze", response_model=AnalysisResponse, summary="Run analysis")
async def analyze(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    registry: SpecialistRegistry = Depends(get_registry),
    settings: Settings = Depends(get_settings),
) -> AnalysisResponse:
    """
    Full analysis pipeline:
    1. Resolve uploaded files
    2. Classify input configuration
    3. Classify intent
    4. Build execution graph
    5. Run specialist(s)
    6. Synthesize evidence
    7. Calculate confidence
    8. Detect disagreement
    9. Generate final answer
    10. Return structured response
    """
    request_id = uuid.uuid4().hex
    start_time = datetime.now(timezone.utc)
    trace = TraceRecorder()

    # --- Persist analysis request ---
    db_request = orm.AnalysisRequest(
        id=request_id,
        session_id=request.session_id,
        query_text=request.query,
        status="processing",
    )
    db.add(db_request)
    db.commit()

    try:
        # --- Step 1: Resolve files ---
        with trace.step(action="Resolve uploaded files", component="file_resolver") as step:
            files = []
            for file_id in request.file_ids:
                db_file = db.query(orm.UploadedFile).filter(orm.UploadedFile.id == file_id).first()
                if not db_file:
                    raise NotFoundError(message=f"File '{file_id}' not found.")
                files.append(db_file)
            step.complete(output_summary=f"Resolved {len(files)} file(s)")

        file_paths = [f.file_path for f in files]
        metadatas = [
            ImageMetadata(**f.metadata_json) if f.metadata_json else ImageMetadata(filename=f.original_filename)
            for f in files
        ]

        # --- Step 2: Classify input configuration ---
        with trace.step(action="Classify input configuration", component="classifier") as step:
            input_config = classify_input_configuration(metadatas)
            step.complete(output_summary=f"Detected: {input_config.value}")

        # --- Step 3: Classify intent ---
        with trace.step(action="Classify query intent", component="planner") as step:
            intent_result = classify_intent(request.query, input_config)
            step.complete(output_summary=f"Intent: {intent_result.type.value} (conf={intent_result.confidence:.2f})")

        # --- Step 4: Build execution graph ---
        with trace.step(action="Build execution graph", component="execution_graph") as step:
            graph = ExecutionGraph(registry)
            route_plan = graph.plan(input_config, intent_result)
            step.complete(output_summary=f"Specialist: {route_plan.specialist}")

        # --- Step 5: Run specialist ---
        specialist_request = SpecialistRequest(
            request_id=request_id,
            specialist_name=route_plan.specialist,
            input_configuration=input_config,
            intent=intent_result.type,
            file_ids=request.file_ids,
            file_paths=file_paths,
            metadata=metadatas,
            query=request.query,
        )

        with trace.step(action=f"Execute specialist: {route_plan.specialist}", component=route_plan.specialist) as step:
            specialist = registry.get_specialist(route_plan.specialist)
            specialist_result = await specialist.execute(specialist_request)
            step.complete(output_summary=f"Status: {specialist_result.status.value}, conf={specialist_result.raw_confidence:.2f}")

        # --- Step 6: Synthesize evidence ---
        with trace.step(action="Synthesize evidence", component="evidence_synthesizer") as step:
            synthesizer = EvidenceSynthesizer()
            evidence = synthesizer.synthesize([specialist_result])
            step.complete(output_summary=f"Evidence items: {len(evidence)}")

        # --- Step 7: Detect disagreement ---
        with trace.step(action="Check for disagreement", component="disagreement_detector") as step:
            detector = DisagreementDetector()
            disagreement = detector.detect([specialist_result])
            step.complete(output_summary=f"Disagreement: {disagreement.detected}")

        # --- Step 8: Calculate confidence ---
        with trace.step(action="Calculate confidence", component="confidence_calculator") as step:
            calculator = ConfidenceCalculator(settings)
            confidence = calculator.calculate(
                input_config=input_config,
                specialist_results=[specialist_result],
                evidence=evidence,
                disagreement=disagreement,
            )
            step.complete(output_summary=f"Score: {confidence.final_score:.2f} ({confidence.label.value})")

        # --- Step 9: Generate answer ---
        with trace.step(action="Synthesize final answer", component="response_synthesizer") as step:
            is_refused = confidence.final_score < settings.CONFIDENCE_THRESHOLD_LOW
            if is_refused:
                answer = AnswerBlock(
                    text="Insufficient evidence to provide a reliable answer.",
                    is_refused=True,
                    refusal_reason=confidence.explanation,
                )
            else:
                answer = AnswerBlock(text=specialist_result.answer)
            step.complete(output_summary="Answer generated" if not is_refused else "Answer refused (low confidence)")

        final_status = AnalysisStatus.INSUFFICIENT_EVIDENCE if is_refused else AnalysisStatus.SUCCESS
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        response = AnalysisResponse(
            request_id=request_id,
            session_id=request.session_id,
            status=final_status,
            input={
                "configuration": input_config.value,
                "files": [f.original_filename for f in files],
            },
            intent=intent_result,
            answer=answer,
            evidence=evidence,
            confidence=confidence,
            disagreement=disagreement,
            execution_trace=trace.steps,
            created_at=start_time,
            duration_ms=duration_ms,
        )

        # --- Persist result ---
        db_request.status = final_status.value
        db_request.input_configuration = input_config.value
        db_request.intent = intent_result.type.value
        db_request.specialist_used = route_plan.specialist
        db_request.confidence_score = confidence.final_score
        db_request.result_json = response.model_dump(mode="json")
        db_request.completed_at = end_time
        db_request.duration_ms = duration_ms
        db.commit()

        logger.info(
            "analysis_complete",
            request_id=request_id,
            status=final_status.value,
            confidence=confidence.final_score,
            duration_ms=duration_ms,
        )

        return response

    except Exception as exc:
        db_request.status = "failed"
        db_request.error_code = getattr(exc, "error_code", "INTERNAL_ERROR")
        db.commit()
        logger.exception("analysis_failed", request_id=request_id)
        raise


@router.get("/analysis/{request_id}", response_model=AnalysisResponse, summary="Get analysis result")
async def get_analysis(
    request_id: str,
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    """Retrieve a previously completed analysis result."""
    db_req = db.query(orm.AnalysisRequest).filter(orm.AnalysisRequest.id == request_id).first()
    if not db_req or not db_req.result_json:
        raise NotFoundError(message=f"Analysis '{request_id}' not found or not yet complete.")
    return AnalysisResponse(**db_req.result_json)


@router.get("/history", summary="Get recent analysis history")
async def get_history_list(
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[dict]:
    """Retrieve recent queries and analysis summaries from database."""
    records = (
        db.query(orm.AnalysisRequest)
        .filter(orm.AnalysisRequest.status == "success")
        .order_by(orm.AnalysisRequest.created_at.desc())
        .limit(limit)
        .all()
    )

    items = []
    for r in records:
        res = r.result_json or {}
        answer = res.get("answer", {}).get("text", "")
        conf_label = res.get("confidence", {}).get("label", "moderate")
        files = res.get("input", {}).get("files", [])

        items.append({
            "id": r.id,
            "query": r.query_text,
            "timestamp": r.created_at.isoformat() if r.created_at else "",
            "task": r.intent or "ANALYSIS",
            "confidenceScore": r.confidence_score or 0.8,
            "confidenceLabel": conf_label,
            "answerSummary": answer[:180] + "..." if len(answer) > 180 else answer,
            "files": files,
            "configuration": r.input_configuration or "SINGLE_OPTICAL",
        })

    return items
