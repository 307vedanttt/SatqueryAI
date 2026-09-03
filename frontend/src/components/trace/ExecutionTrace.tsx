import React, { useState } from 'react';
import type { ExecutionStep } from '../../types';

interface ExecutionTraceProps {
  steps: ExecutionStep[];
}

export const ExecutionTrace: React.FC<ExecutionTraceProps> = ({ steps }) => {
  const [isOpen, setIsOpen] = useState(true);

  if (!steps || steps.length === 0) {
    return null;
  }

  const completedCount = steps.filter((s) => s.status === 'success').length;

  return (
    <div className="execution-trace card p-4 bg-surface rounded-xl border border-glass-border shadow-lg">
      <div
        className="flex justify-between items-center cursor-pointer select-none"
        onClick={() => setIsOpen(!isOpen)}
        role="button"
        tabIndex={0}
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2">
          <span className="text-base">📋</span>
          <span className="text-xs font-bold text-text uppercase tracking-wider">
            EXECUTION TRACE
          </span>
          <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/40">
            {completedCount}/{steps.length} STEPS COMPLETED ✓
          </span>
        </div>

        <button
          type="button"
          className="text-xs text-text-3 hover:text-text p-1 font-mono"
          aria-label={isOpen ? 'Collapse execution trace' : 'Expand execution trace'}
        >
          {isOpen ? '▲ Collapse' : '▼ Expand'}
        </button>
      </div>

      {isOpen && (
        <div className="trace-steps mt-3 pt-3 border-t border-glass-border/40 space-y-2.5 font-mono text-xs">
          {steps.map((step) => {
            const isSuccess = step.status === 'success';
            const isFailed = step.status === 'failed';
            const statusIcon = isSuccess ? '✓' : isFailed ? '✕' : '●';
            const stepNum = String(step.step_index).padStart(2, '0');

            return (
              <div
                key={step.step_id || step.step_index}
                className="trace-step flex items-start gap-3 p-2.5 rounded-lg bg-surface-2/60 border border-glass-border/30 hover:border-glass-border transition-colors"
              >
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0 mt-0.5 ${
                    isSuccess
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-700/50'
                      : isFailed
                      ? 'bg-red-950 text-red-400 border border-red-700/50'
                      : 'bg-blue-950 text-blue-400 border border-blue-700/50'
                  }`}
                >
                  {statusIcon}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center justify-between gap-1">
                    <div className="flex items-center gap-2">
                      <span className="text-text-3 font-semibold">{stepNum}</span>
                      <span className="text-text font-bold text-xs">{step.action}</span>
                    </div>

                    <div className="flex items-center gap-2 text-[10px] text-text-3">
                      <span className="px-1.5 py-0.2 rounded bg-surface border border-glass-border">
                        {step.component}
                      </span>
                      {step.duration_ms !== null && (
                        <span>{step.duration_ms} ms</span>
                      )}
                    </div>
                  </div>

                  {step.output_summary && (
                    <div className="text-[11px] text-text-2 mt-1 pl-6 leading-relaxed">
                      {step.output_summary}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
