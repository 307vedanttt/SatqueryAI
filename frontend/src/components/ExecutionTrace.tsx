import React from 'react';
import type { ExecutionStep } from '../types';

interface ExecutionTraceProps {
  steps: ExecutionStep[];
}

export const ExecutionTrace: React.FC<ExecutionTraceProps> = ({ steps }) => {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="card mt-3">
      <div className="card-title">
        <span className="icon">⚙️</span>
        <span>Execution Trace</span>
      </div>

      <div className="trace-list">
        {steps.map((step) => {
          const isSuccess = step.status === 'success';
          const isFailed = step.status === 'failed';

          return (
            <div key={step.step_id} className="trace-step">
              <div className={`trace-dot ${step.status}`}>
                {isSuccess ? '✓' : isFailed ? '✕' : '•'}
              </div>
              <div className="trace-content">
                <div className="trace-action">{step.action}</div>
                <div className="trace-meta">
                  <span>{step.component}</span>
                  {step.duration_ms !== null && (
                    <span className="trace-duration">{step.duration_ms}ms</span>
                  )}
                  {step.output_summary && (
                    <span className="text-text-2">— {step.output_summary}</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
