"""
agent/executor.py — Bounded Execution Engine for SatQuery AI

This module implements the "brain" of the agentic system: the component that
takes a SpecialistRequest, decides which tool to call, validates inputs, runs
the tool, and returns a fully populated SpecialistResponse and ExecutionTrace.

BOUNDED EXECUTION DESIGN
--------------------------
A central design constraint of SatQuery AI is that the agent must be
BOUNDED and DETERMINISTIC. This directly implements the problem statement's
requirement for an "auditable execution summary" and mitigates the documented
failure modes of open-ended agentic systems:

  * Tool-selection errors (mitigated: Router uses deterministic rules)
  * Malformed tool arguments (mitigated: Pydantic contracts validated before call)
  * Infinite planning loops (mitigated: MAX_STEPS hard ceiling enforced in code)
  * Excessive retries on invalid inputs (mitigated: retries only on runtime
    exceptions, never on precondition failures)

KEY CONSTANTS
-------------
MAX_STEPS = 6   Total step budget across an entire Executor.run() call.
                If this limit would be exceeded, execution stops immediately
                and returns status="error", confidence_tier="insufficient".

MAX_RETRIES = 2 Maximum number of retries after the initial attempt fails.
                So the tool callable is invoked at most 3 times total.
                Retries are only for runtime/IO exceptions, not for
                precondition failures (those are rejected immediately).

EXECUTION FLOW (Steps 1–7)
---------------------------
Step 1: Validate input metadata (basic null/sanity checks)
Step 2: Classify intent via Router.classify() → tool name
Step 3: Look up tool in ToolRegistry; run precondition check
Step 4: If precondition fails → log failure, return error immediately (no retry)
Step 5: Execute tool callable in try/except, retry up to MAX_RETRIES on exception
Step 6: Enforce MAX_STEPS — stop if budget exceeded
Step 7: Return SpecialistResponse + ExecutionTrace on success
"""

import logging
from typing import Optional

from agent.registry import ToolRegistry
from agent.router import Router
from schemas.contracts import (
    ExecutionStep,
    ExecutionTrace,
    ImageMetadata,
    SpecialistRequest,
    SpecialistResponse,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Execution constants — fixed in code, not left to model discretion
# ---------------------------------------------------------------------------

MAX_STEPS: int = 6
"""
Hard ceiling on total execution steps per run().
Enforced to prevent unbounded loops. If exceeded, execution aborts with
status="error" and confidence_tier="insufficient" rather than continuing.
"""

MAX_RETRIES: int = 2
"""
Maximum number of retries after the initial tool execution attempt.
Total attempts = MAX_RETRIES + 1 = 3.
Retries apply ONLY to runtime exceptions (e.g. OOM, IO error).
Precondition failures are NEVER retried — they indicate invalid input.
"""


# ---------------------------------------------------------------------------
# Error response helper
# ---------------------------------------------------------------------------

def _error_response(
    task: str,
    message: str,
    confidence_tier: str = "insufficient",
) -> SpecialistResponse:
    """
    Build a SpecialistResponse for an error/abort case.

    Args:
        task: Tool name or best guess for the task field.
        message: Human-readable error description.
        confidence_tier: Confidence tier; defaults to "insufficient".

    Returns:
        SpecialistResponse with status="error".
    """
    return SpecialistResponse(
        task=task,
        answer="",
        confidence=0.0,
        confidence_tier=confidence_tier,
        bounding_boxes=[],
        evidence="",
        model_used="",
        status="error",
        error_message=message,
    )


def _validate_image_metadata(images: list[ImageMetadata]) -> tuple[bool, str]:
    """
    Basic inline metadata validation.

    Checks that each image has a non-empty sensor field and a non-empty
    file_path. Width/height/bands are not required because benchmark images
    (PNG/JPEG) may not populate these fields.

    This will be replaced by a call to remote_sensing.metadata.validate_metadata_complete
    once Person D's module is merged. Until then, these null-checks cover
    the critical invariants the router and preconditions depend on.

    Args:
        images: List of ImageMetadata to validate.

    Returns:
        (True, "") if all images pass basic checks.
        (False, reason) with an explanation of the first failure found.
    """
    if not images:
        return False, "No images provided. At least one image is required."

    for i, img in enumerate(images):
        if not img.sensor or not img.sensor.strip():
            return False, (
                f"Image {i + 1} is missing the 'sensor' field. "
                "Sensor must be 'optical', 'sar', or 'multispectral'."
            )
        if not img.file_path or not img.file_path.strip():
            return False, (
                f"Image {i + 1} is missing 'file_path'. "
                "A valid file path is required for processing."
            )

    return True, ""


class Executor:
    """
    Bounded execution engine.

    Constructs a fully auditable ExecutionTrace for every run() call.
    Each major decision point (validation, routing, precondition, execution,
    retry, abort) is recorded as an ExecutionStep so the full reasoning
    chain is visible in the UI.

    Usage:
        executor = Executor()
        response, trace = executor.run(request)
    """

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        router: Optional[Router] = None,
    ) -> None:
        """
        Initialise the executor.

        Args:
            registry: ToolRegistry instance. Defaults to a fresh ToolRegistry
                      with all six stub-registered tools.
            router: Router instance. Defaults to a fresh Router.
        """
        self._registry = registry or ToolRegistry()
        self._router = router or Router()

    def run(
        self, request: SpecialistRequest
    ) -> tuple[SpecialistResponse, ExecutionTrace]:
        """
        Execute the full bounded analysis pipeline for one request.

        This method is the single entry point. It:
          1. Validates image metadata
          2. Routes to the correct tool
          3. Checks the tool's precondition
          4. Executes the tool (with retries for runtime errors)
          5. Enforces the MAX_STEPS budget at every step
          6. Returns both the response and the full execution trace

        Args:
            request: The SpecialistRequest to process.

        Returns:
            (SpecialistResponse, ExecutionTrace) — always returned, even on error.
            Check response.status == "error" to detect failure cases.
        """
        steps: list[ExecutionStep] = []
        tool_name: str = "unknown"

        def _append_step(
            action: str,
            result_summary: str,
            tool_used: Optional[str] = None,
        ) -> None:
            """Append a new ExecutionStep to steps list."""
            step = ExecutionStep(
                step_number=len(steps) + 1,
                action=action,
                tool_used=tool_used,
                result_summary=result_summary,
            )
            steps.append(step)
            logger.info(
                "Step %d: %s | %s",
                step.step_number,
                action,
                result_summary,
            )

        def _build_trace(final_tier: str) -> ExecutionTrace:
            """Build the final ExecutionTrace from accumulated steps."""
            return ExecutionTrace(
                query=request.query,
                intent_classified=tool_name,
                steps=steps,
                final_confidence_tier=final_tier,
                total_steps=len(steps),
            )

        def _step_limit_exceeded() -> bool:
            """Return True if adding another step would exceed MAX_STEPS."""
            return len(steps) >= MAX_STEPS

        logger.info(
            "Executor.run started: query=%r, n_images=%d",
            request.query[:80],
            len(request.images),
        )

        # ------------------------------------------------------------------ #
        # STEP 1 — Validate input metadata                                    #
        # ------------------------------------------------------------------ #
        is_valid, validation_reason = _validate_image_metadata(request.images)
        if not is_valid:
            _append_step(
                action="Validate input metadata",
                result_summary=f"FAILED: {validation_reason}",
            )
            logger.warning("Metadata validation failed: %s", validation_reason)
            return (
                _error_response("unknown", validation_reason),
                _build_trace("insufficient"),
            )

        img_summary = (
            f"{len(request.images)} image(s): "
            + ", ".join(f"{img.sensor}@{img.file_path}" for img in request.images)
        )
        _append_step(
            action="Validate input metadata",
            result_summary=f"OK — {img_summary}",
        )

        # ------------------------------------------------------------------ #
        # STEP 2 — Route / classify intent                                    #
        # ------------------------------------------------------------------ #
        if _step_limit_exceeded():
            msg = f"Step limit ({MAX_STEPS}) reached before routing."
            _append_step("Step limit enforcement", f"ABORT — {msg}")
            logger.error(msg)
            return _error_response(tool_name, msg), _build_trace("insufficient")

        try:
            tool_name = self._router.classify(
                query=request.query,
                images=request.images,
            )
        except ValueError as exc:
            _append_step(
                action="Classify intent (router)",
                result_summary=f"FAILED — {exc}",
            )
            logger.warning("Router.classify raised ValueError: %s", exc)
            return (
                _error_response("unknown", str(exc)),
                _build_trace("insufficient"),
            )

        _append_step(
            action="Classify intent (router)",
            result_summary=f"Routed to tool: {tool_name}",
            tool_used=tool_name,
        )

        # ------------------------------------------------------------------ #
        # STEP 3 — Look up tool and run precondition check                   #
        # ------------------------------------------------------------------ #
        if _step_limit_exceeded():
            msg = f"Step limit ({MAX_STEPS}) reached before precondition check."
            _append_step("Step limit enforcement", f"ABORT — {msg}")
            logger.error(msg)
            return _error_response(tool_name, msg), _build_trace("insufficient")

        try:
            precondition_ok, precondition_reason = self._registry.check_precondition(
                tool_name, request
            )
        except KeyError as exc:
            _append_step(
                action=f"Precondition check: {tool_name}",
                result_summary=f"FAILED — tool not found: {exc}",
                tool_used=tool_name,
            )
            logger.error("Tool not found in registry: %s", exc)
            return (
                _error_response(tool_name, str(exc)),
                _build_trace("insufficient"),
            )

        # ------------------------------------------------------------------ #
        # STEP 4 — Abort immediately on precondition failure (no retry)      #
        # ------------------------------------------------------------------ #
        if not precondition_ok:
            _append_step(
                action=f"Precondition check: {tool_name}",
                result_summary=f"REJECTED — {precondition_reason}",
                tool_used=tool_name,
            )
            logger.warning(
                "Precondition failed for tool '%s': %s", tool_name, precondition_reason
            )
            # Precondition failures are NOT retried — the input is invalid.
            # Retrying with invalid input would produce the same failure repeatedly.
            return (
                _error_response(
                    tool_name,
                    f"Precondition failed: {precondition_reason}",
                ),
                _build_trace("insufficient"),
            )

        _append_step(
            action=f"Precondition check: {tool_name}",
            result_summary="PASSED",
            tool_used=tool_name,
        )

        # ------------------------------------------------------------------ #
        # STEP 5 — Execute tool with retry on runtime exception              #
        # ------------------------------------------------------------------ #
        callable_fn = self._registry.get_callable(tool_name)
        response: Optional[SpecialistResponse] = None
        last_error: Optional[str] = None
        attempt = 0
        total_attempts = MAX_RETRIES + 1  # e.g. 3 attempts maximum

        while attempt < total_attempts:
            # ----------------------------------------------------------------
            # STEP 6 — Enforce MAX_STEPS budget before each attempt
            # ----------------------------------------------------------------
            if _step_limit_exceeded():
                msg = (
                    f"Step limit ({MAX_STEPS}) reached during tool execution "
                    f"(attempt {attempt + 1}/{total_attempts})."
                )
                _append_step(
                    action="Step limit enforcement",
                    result_summary=f"ABORT — {msg}",
                    tool_used=tool_name,
                )
                logger.error(msg)
                return _error_response(tool_name, msg), _build_trace("insufficient")

            attempt += 1
            action_label = f"Execute {tool_name} (attempt {attempt}/{total_attempts})"

            try:
                logger.info("Calling tool '%s', attempt %d", tool_name, attempt)
                response = callable_fn(request)

                _append_step(
                    action=action_label,
                    result_summary=f"SUCCESS — confidence_tier={response.confidence_tier}",
                    tool_used=tool_name,
                )
                break  # Success — exit retry loop

            except Exception as exc:  # noqa: BLE001
                last_error = f"{type(exc).__name__}: {exc}"
                logger.warning(
                    "Tool '%s' raised exception on attempt %d/%d: %s",
                    tool_name, attempt, total_attempts, last_error,
                )
                _append_step(
                    action=action_label,
                    result_summary=f"FAILED — {last_error}",
                    tool_used=tool_name,
                )

                if attempt >= total_attempts:
                    # All attempts exhausted
                    msg = (
                        f"Tool '{tool_name}' failed after {total_attempts} attempt(s). "
                        f"Last error: {last_error}"
                    )
                    logger.error(msg)
                    return _error_response(tool_name, msg), _build_trace("insufficient")
                # Otherwise continue to next attempt

        # ------------------------------------------------------------------ #
        # STEP 7 — Return successful response + complete trace               #
        # ------------------------------------------------------------------ #
        assert response is not None  # Guaranteed by loop logic above
        trace = _build_trace(response.confidence_tier)

        logger.info(
            "Executor.run completed: tool=%s, status=%s, steps=%d",
            tool_name,
            response.status,
            len(steps),
        )
        return response, trace
