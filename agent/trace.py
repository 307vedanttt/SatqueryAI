"""
agent/trace.py — Execution Trace Formatters

Provides two views of an ExecutionTrace:
  1. format_trace_for_display() — human-readable multi-line string for the demo UI
  2. format_trace_as_dict()    — JSON-serializable dict for the API response

These functions are intentionally pure (no side effects) so they can be
called from any context: FastAPI route handlers, Gradio callbacks, scripts.
"""

from schemas.contracts import ExecutionTrace

# Confidence tier → display label
_TIER_LABELS: dict[str, str] = {
    "high": "HIGH ✅",
    "moderate": "MODERATE 🟡",
    "insufficient": "INSUFFICIENT 🔴",
}


def format_trace_for_display(trace: ExecutionTrace) -> str:
    """
    Render an ExecutionTrace as a clean, human-readable multi-line string.

    This output is shown directly in the demo UI (Gradio accordion or
    frontend collapsible section) so judges can audit the full reasoning chain.

    Format example:
        Query: "Has the water body changed between these dates?"
        Intent classified: change_vqa

        Execution steps:
          1. Validated input metadata (2 images, matching sensor/CRS)
          2. Classified intent → change_vqa
          3. Precondition check: change_vqa — PASSED
          4. Execute change_vqa (attempt 1/3) — SUCCESS

        Final confidence: HIGH ✅
        Total steps: 4 / 6 maximum

    Args:
        trace: The ExecutionTrace returned by Executor.run().

    Returns:
        Multi-line string suitable for display in any text area.
    """
    lines: list[str] = []

    lines.append(f'Query: "{trace.query}"')
    lines.append(f"Intent classified: {trace.intent_classified}")
    lines.append("")
    lines.append("Execution steps:")

    for step in trace.steps:
        tool_part = f" [{step.tool_used}]" if step.tool_used else ""
        lines.append(
            f"  {step.step_number}. {step.action}{tool_part}"
            f"\n       → {step.result_summary}"
        )

    lines.append("")
    tier_display = _TIER_LABELS.get(trace.final_confidence_tier, trace.final_confidence_tier.upper())
    lines.append(f"Final confidence: {tier_display}")
    lines.append(f"Total steps: {trace.total_steps} / {6} maximum")

    return "\n".join(lines)


def format_trace_as_dict(trace: ExecutionTrace) -> dict:
    """
    Return a JSON-serializable dict representation of an ExecutionTrace.

    This is the structured form used in API responses so the frontend can
    display the trace programmatically (e.g. render each step as a row in a
    table, colour-code success/failure steps, etc.).

    The dict has the following shape:
        {
            "query": str,
            "intent_classified": str,
            "steps": [
                {
                    "step_number": int,
                    "action": str,
                    "tool_used": str | None,
                    "result_summary": str,
                },
                ...
            ],
            "final_confidence_tier": str,
            "final_confidence_label": str,   # human-readable label
            "total_steps": int,
            "max_steps": int,
        }

    Args:
        trace: The ExecutionTrace returned by Executor.run().

    Returns:
        JSON-serializable dict.
    """
    return {
        "query": trace.query,
        "intent_classified": trace.intent_classified,
        "steps": [
            {
                "step_number": step.step_number,
                "action": step.action,
                "tool_used": step.tool_used,
                "result_summary": step.result_summary,
            }
            for step in trace.steps
        ],
        "final_confidence_tier": trace.final_confidence_tier,
        "final_confidence_label": _TIER_LABELS.get(
            trace.final_confidence_tier, trace.final_confidence_tier.upper()
        ),
        "total_steps": trace.total_steps,
        "max_steps": 6,
    }
