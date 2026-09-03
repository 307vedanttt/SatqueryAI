"""
SatQuery AI — Trace Formatter

Converts execution trace steps into human-readable text format
for display in the UI and documentation.
"""

from app.models.schemas import ExecutionStep, ExecutionStepStatus

_STATUS_ICONS = {
    ExecutionStepStatus.SUCCESS: "✓",
    ExecutionStepStatus.FAILED: "✗",
    ExecutionStepStatus.SKIPPED: "○",
    ExecutionStepStatus.IN_PROGRESS: "…",
}


def format_trace_text(steps: list[ExecutionStep]) -> str:
    """Format execution trace as human-readable text."""
    if not steps:
        return "No execution trace available."

    lines = ["Execution Trace", "=" * 40]
    for step in steps:
        icon = _STATUS_ICONS.get(step.status, "?")
        duration = f"{step.duration_ms}ms" if step.duration_ms is not None else "—"
        lines.append(f"\n{icon} Step {step.step_index + 1}: {step.action}")
        lines.append(f"  Component : {step.component}")
        lines.append(f"  Status    : {step.status.value}")
        lines.append(f"  Duration  : {duration}")
        if step.output_summary:
            lines.append(f"  Output    : {step.output_summary}")

    total_ms = sum(s.duration_ms or 0 for s in steps)
    lines.append(f"\nTotal: {len(steps)} steps, {total_ms}ms")
    return "\n".join(lines)


def format_trace_summary(steps: list[ExecutionStep]) -> str:
    """Compact one-line summary of the trace."""
    n = len(steps)
    failed = sum(1 for s in steps if s.status == ExecutionStepStatus.FAILED)
    total_ms = sum(s.duration_ms or 0 for s in steps)
    status = "completed" if failed == 0 else f"{failed} step(s) failed"
    return f"{n} steps — {status} — {total_ms}ms total"
