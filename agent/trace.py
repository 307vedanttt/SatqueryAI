"""
SatQuery AI — Execution Trace Formatter (Person A)

Provides formatters for UI display string rendering and JSON dictionary responses.
"""

from schemas.contracts import ExecutionTrace


def format_trace_for_display(trace: ExecutionTrace) -> str:
    """Format execution trace into human-readable text for UI demo."""
    lines = [
        f'Query: "{trace.query}"',
        f"Intent classified: {trace.intent_classified}",
        "",
        "Execution steps:",
    ]

    for step in trace.steps:
        lines.append(f"  {step.step_number}. {step.action} -> {step.result_summary}")

    tier_upper = (trace.final_confidence_tier or "INSUFFICIENT").upper()
    lines.append("")
    lines.append(f"Final confidence: {tier_upper}")
    lines.append(f"Total steps: {trace.total_steps} / 6 maximum")

    return "\n".join(lines)


def format_trace_as_dict(trace: ExecutionTrace) -> dict:
    """Return JSON-serializable dictionary representation of the trace."""
    return trace.model_dump(mode="json")
