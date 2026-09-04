import pytest
from app.trace.execution import TraceRecorder
from app.models.schemas import ExecutionStepStatus

def test_successful_execution():
    trace = TraceRecorder(analysis_id="test-id")
    with trace.step("Input Validation", "system") as step:
        step.complete("Validated 2 images")
        
    with trace.step("Model Execution", "mock_specialist") as step:
        step.complete("Output generated")
        
    assert len(trace.steps) == 2
    
    assert trace.steps[0].analysis_id == "test-id"
    assert trace.steps[0].step == "Input Validation"
    assert trace.steps[0].status == ExecutionStepStatus.SUCCESS
    assert trace.steps[0].explanation == "Validated 2 images"
    
    assert trace.steps[1].specialist == "mock_specialist"
    assert trace.steps[1].status == ExecutionStepStatus.SUCCESS
    assert trace.steps[1].explanation == "Output generated"
    assert trace.steps[1].error is None

def test_failed_execution():
    trace = TraceRecorder(analysis_id="fail-id")
    try:
        with trace.step("Model Execution", "mock_specialist") as step:
            raise ValueError("Something went terribly wrong!")
    except ValueError:
        pass
        
    assert len(trace.steps) == 1
    assert trace.steps[0].status == ExecutionStepStatus.FAILED
    assert "ValueError" in trace.steps[0].error
    assert "terribly wrong" in trace.steps[0].error
    # Must NOT expose stack traces, just error type and message

def test_partial_execution():
    trace = TraceRecorder(analysis_id="partial-id")
    with trace.step("Step 1", "system") as step:
        step.complete("Done 1")
    
    try:
        with trace.step("Step 2", "system") as step:
            raise KeyError("Missing config")
    except KeyError:
        pass
        
    assert len(trace.steps) == 2
    assert trace.steps[0].status == ExecutionStepStatus.SUCCESS
    assert trace.steps[1].status == ExecutionStepStatus.FAILED

def test_trace_ordering():
    trace = TraceRecorder(analysis_id="order-id")
    for i in range(5):
        with trace.step(f"Step {i}", "system") as step:
            step.complete(f"Done {i}")
            
    assert len(trace.steps) == 5
    for i in range(5):
        assert trace.steps[i].step_index == i
        assert trace.steps[i].step == f"Step {i}"

def test_missing_analysis_id():
    # It should still record steps gracefully even if an analysis_id wasn't available yet
    trace = TraceRecorder()
    with trace.step("Step 1", "system") as step:
        step.complete("Done")
    
    assert trace.steps[0].analysis_id is None
    assert trace.steps[0].status == ExecutionStepStatus.SUCCESS
