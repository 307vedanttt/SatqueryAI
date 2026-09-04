"""
SatQuery AI — Execution Trace Recorder

Records each step of the analysis pipeline as a typed ExecutionStep.
The trace is included in the final response for auditability.

What IS exposed in the trace:
  - Task name (human-readable)
  - Component name
  - Status (success/failed)
  - Duration in milliseconds
  - Brief output summary

What is NOT exposed:
  - Raw LLM chain-of-thought
  - API keys or credentials
  - Internal stack traces
  - Raw provider responses
"""

import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator

from app.models.schemas import ExecutionStep, ExecutionStepStatus


class _StepContext:
    """Context manager for a single trace step."""

    def __init__(self, recorder: "TraceRecorder", action: str, component: str) -> None:
        self._recorder = recorder
        self._action = action
        self._component = component
        self._start = time.monotonic()
        self._step_index = len(recorder.steps)
        self._output_summary: str | None = None
        self._error: str | None = None
        self._status: ExecutionStepStatus = ExecutionStepStatus.IN_PROGRESS

    def complete(self, output_summary: str | None = None) -> None:
        """Mark step as successfully completed."""
        self._output_summary = output_summary
        self._status = ExecutionStepStatus.SUCCESS

    def fail(self, reason: str | None = None) -> None:
        """Mark step as failed."""
        self._error = reason
        self._status = ExecutionStepStatus.FAILED

    def __enter__(self) -> "_StepContext":
        self._status = ExecutionStepStatus.IN_PROGRESS
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        duration_ms = int((time.monotonic() - self._start) * 1000)

        if exc_type is not None:
            self._status = ExecutionStepStatus.FAILED
            self._error = f"Error: {type(exc_val).__name__} - {str(exc_val)}"
            # Ensure we don't expose stack traces per requirements

        step = ExecutionStep(
            analysis_id=self._recorder.analysis_id,
            step_id=uuid.uuid4().hex,
            step_index=self._step_index,
            timestamp=datetime.now(timezone.utc),
            step=self._action,
            specialist=self._component,
            status=self._status,
            duration_ms=duration_ms,
            explanation=self._output_summary,
            error=self._error,
        )
        self._recorder.steps.append(step)

        # Re-raise exceptions — the trace records them but doesn't suppress
        return False


class TraceRecorder:
    """Records the full execution trace for an analysis request."""

    def __init__(self, analysis_id: str | None = None) -> None:
        self.analysis_id = analysis_id
        self.steps: list[ExecutionStep] = []

    def step(self, action: str, component: str) -> _StepContext:
        """Context manager to record a single execution step."""
        return _StepContext(self, action, component)

    def to_dict(self) -> list[dict]:
        return [s.model_dump(mode="json") for s in self.steps]
