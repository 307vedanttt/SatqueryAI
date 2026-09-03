"""
SatQuery AI — Bounded Execution Engine (Person A)

Bounded-Execution Design Rationale:
  This module implements a strictly bounded, deterministic execution graph with fixed max retries
  (MAX_RETRIES = 2, i.e., 3 attempts maximum) and a hard cap on total steps (MAX_STEPS = 6).
  This directly fulfills SIH26167's requirement for an auditable execution summary while preventing
  infinite planning loops, tool hallucination, or malformed call recursion.
"""

import logging
from typing import Tuple
from agent.registry import ToolRegistry
from agent.router import Router
from schemas.contracts import (
    ExecutionStep,
    ExecutionTrace,
    SpecialistRequest,
    SpecialistResponse,
)

logger = logging.getLogger("satquery.agent.executor")

MAX_RETRIES = 2
MAX_STEPS = 6


class Executor:
    """Bounded, auditable execution engine."""

    def __init__(self, registry: ToolRegistry = None, router: Router = None):
        self.registry = registry or ToolRegistry()
        self.router = router or Router()

    def run(self, request: SpecialistRequest) -> Tuple[SpecialistResponse, ExecutionTrace]:
        steps: list[ExecutionStep] = []
        step_counter = 1

        def add_step(action: str, tool_used: str, result_summary: str) -> ExecutionStep:
            nonlocal step_counter
            step = ExecutionStep(
                step_number=step_counter,
                action=action,
                tool_used=tool_used,
                result_summary=result_summary,
            )
            steps.append(step)
            logger.info(f"Step {step_counter} [{tool_used}]: {action} -> {result_summary}")
            step_counter += 1
            return step

        # Step 1: Validate images
        logger.info(f"Starting execution for query: '{request.query}' with {len(request.images)} image(s)")
        if not request.images:
            add_step("Validate input images", "validation_helper", "Failed: No images provided")
            resp = SpecialistResponse(
                task="none",
                answer="Execution aborted: No images provided in request.",
                confidence=0.0,
                confidence_tier="insufficient",
                status="error",
                error_message="No images provided in request.",
            )
            trace = ExecutionTrace(
                query=request.query,
                intent_classified="none",
                steps=steps,
                final_confidence_tier="insufficient",
                total_steps=len(steps),
            )
            return resp, trace

        # Null check on metadata
        invalid_meta = any(not img.file_path for img in request.images)
        if invalid_meta:
            add_step("Validate input images", "validation_helper", "Failed: Missing image file_path")
            resp = SpecialistResponse(
                task="none",
                answer="Execution aborted: ImageMetadata incomplete (missing file_path).",
                confidence=0.0,
                confidence_tier="insufficient",
                status="error",
                error_message="ImageMetadata incomplete (missing file_path).",
            )
            trace = ExecutionTrace(
                query=request.query,
                intent_classified="none",
                steps=steps,
                final_confidence_tier="insufficient",
                total_steps=len(steps),
            )
            return resp, trace

        add_step("Validate input images", "validation_helper", f"Passed: {len(request.images)} image(s) verified")

        # Step 2: Route / Classify
        try:
            intent = self.router.classify(request.query, request.images)
            add_step("Classify intent and route query", intent, f"Classified intent as '{intent}'")
        except ValueError as e:
            add_step("Classify intent and route query", "router", f"Routing failed: {str(e)}")
            resp = SpecialistResponse(
                task="unrouted",
                answer=f"Routing error: {str(e)}",
                confidence=0.0,
                confidence_tier="insufficient",
                status="error",
                error_message=str(e),
            )
            trace = ExecutionTrace(
                query=request.query,
                intent_classified="none",
                steps=steps,
                final_confidence_tier="insufficient",
                total_steps=len(steps),
            )
            return resp, trace

        # Step 3 & 4: Lookup tool and check preconditions
        try:
            tool_entry = self.registry.get_tool(intent)
        except KeyError as e:
            add_step("Lookup tool in registry", intent, f"Registry error: {str(e)}")
            resp = SpecialistResponse(
                task=intent,
                answer=f"Tool lookup error: {str(e)}",
                confidence=0.0,
                confidence_tier="insufficient",
                status="error",
                error_message=str(e),
            )
            trace = ExecutionTrace(
                query=request.query,
                intent_classified=intent,
                steps=steps,
                final_confidence_tier="insufficient",
                total_steps=len(steps),
            )
            return resp, trace

        is_valid, reason = tool_entry.precondition_fn(request)
        if not is_valid:
            add_step("Check tool preconditions", intent, f"Precondition failed: {reason}")
            logger.warning(f"Precondition failed for tool '{intent}': {reason}")
            resp = SpecialistResponse(
                task=intent,
                answer=f"Precondition check failed for '{intent}': {reason}",
                confidence=0.0,
                confidence_tier="insufficient",
                status="error",
                error_message=reason,
            )
            trace = ExecutionTrace(
                query=request.query,
                intent_classified=intent,
                steps=steps,
                final_confidence_tier="insufficient",
                total_steps=len(steps),
            )
            return resp, trace

        add_step("Check tool preconditions", intent, f"Passed: {reason}")

        # Step 5 & 6: Execute tool with retries & max step limit
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            if len(steps) >= MAX_STEPS:
                add_step("Step limit check", intent, f"Error: Maximum step limit reached ({MAX_STEPS})")
                logger.error(f"Step limit of {MAX_STEPS} reached during execution.")
                resp = SpecialistResponse(
                    task=intent,
                    answer="Execution error: Step limit reached before tool completion.",
                    confidence=0.0,
                    confidence_tier="insufficient",
                    status="error",
                    error_message=f"Maximum step limit of {MAX_STEPS} reached.",
                )
                trace = ExecutionTrace(
                    query=request.query,
                    intent_classified=intent,
                    steps=steps,
                    final_confidence_tier="insufficient",
                    total_steps=len(steps),
                )
                return resp, trace

            try:
                attempt_action = f"Execute tool '{intent}' (attempt {attempt + 1}/{MAX_RETRIES + 1})"
                logger.info(attempt_action)
                response = tool_entry.callable_fn(request)

                if response.status == "success":
                    add_step(attempt_action, intent, f"Success: {response.answer[:60]}...")
                    trace = ExecutionTrace(
                        query=request.query,
                        intent_classified=intent,
                        steps=steps,
                        final_confidence_tier=response.confidence_tier,
                        total_steps=len(steps),
                    )
                    return response, trace
                else:
                    last_error = response.error_message or "Tool returned status=error"
                    add_step(attempt_action, intent, f"Attempt failed: {last_error}")

            except Exception as e:
                last_error = str(e)
                add_step(attempt_action, intent, f"Exception: {last_error}")
                logger.warning(f"Attempt {attempt + 1} for '{intent}' raised exception: {last_error}")

        # All retries exhausted
        resp = SpecialistResponse(
            task=intent,
            answer=f"Execution failed after {MAX_RETRIES + 1} attempts.",
            confidence=0.0,
            confidence_tier="insufficient",
            status="error",
            error_message=f"All attempts failed. Last error: {last_error}",
        )
        trace = ExecutionTrace(
            query=request.query,
            intent_classified=intent,
            steps=steps,
            final_confidence_tier="insufficient",
            total_steps=len(steps),
        )
        return resp, trace
