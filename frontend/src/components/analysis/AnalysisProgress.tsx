import React, { useEffect, useRef, useState } from 'react';
import type { AnalysisResponse, ExecutionStep } from '../../types';

interface AnalysisProgressProps {
  isAnalyzing: boolean;
  result?: AnalysisResponse | null;
  error?: string | null;
}

interface PipelineStage {
  id: string;
  label: string;
  description: string;
  minMs: number; // minimum elapsed ms before this stage can appear "active"
}

const PIPELINE: PipelineStage[] = [
  { id: 'validation',    label: 'Input Validation',       description: 'CRS check · bounds · format',           minMs: 0    },
  { id: 'config',        label: 'Configuration Detection', description: 'Modality · sensor pair · scene count',   minMs: 400  },
  { id: 'intent',        label: 'Intent Detection',        description: 'Query understanding · routing',          minMs: 900  },
  { id: 'specialist',    label: 'Specialist Selection',    description: 'Routing to bounded execution graph',      minMs: 1500 },
  { id: 'model',         label: 'Model Execution',         description: 'Remote-sensing inference engine',        minMs: 2400 },
  { id: 'evidence',      label: 'Evidence Synthesis',      description: 'Extracting spatial evidence',            minMs: 3600 },
  { id: 'confidence',    label: 'Confidence Calculation',  description: 'Agreement · reliability scoring',        minMs: 4600 },
  { id: 'result',        label: 'Result Ready',            description: 'Grounding response & serialisation',     minMs: 5400 },
];

type StageStatus = 'done' | 'active' | 'pending' | 'error';

function getStageStatuses(elapsedMs: number, hasError: boolean): StageStatus[] {
  if (hasError) {
    return PIPELINE.map((stage, _idx) => {
      if (elapsedMs > stage.minMs + 400) return 'done';
      if (elapsedMs > stage.minMs) return 'error';
      return 'pending';
    });
  }
  return PIPELINE.map((stage, idx) => {
    const next = PIPELINE[idx + 1];
    if (next && elapsedMs > next.minMs) return 'done';
    if (elapsedMs > stage.minMs) return 'active';
    return 'pending';
  });
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

// Map backend ExecutionStep component names to our pipeline stage IDs
function mapTraceToStage(trace: ExecutionStep[]): Record<string, ExecutionStep> {
  const map: Record<string, ExecutionStep> = {};
  for (const step of trace) {
    const comp = (step.component || '').toLowerCase();
    const action = (step.action || '').toLowerCase();
    if (comp.includes('input') || action.includes('validation')) map['validation'] = step;
    else if (comp.includes('config') || action.includes('config')) map['config'] = step;
    else if (comp.includes('intent') || action.includes('intent')) map['intent'] = step;
    else if (comp.includes('specialist') || action.includes('select')) map['specialist'] = step;
    else if (comp.includes('model') || action.includes('inference') || action.includes('execution')) map['model'] = step;
    else if (comp.includes('evidence') || action.includes('evidence')) map['evidence'] = step;
    else if (comp.includes('confidence') || action.includes('confidence')) map['confidence'] = step;
    else if (comp.includes('result') || action.includes('result')) map['result'] = step;
  }
  return map;
}

export const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  isAnalyzing,
  result,
  error,
}) => {
  const [elapsedMs, setElapsedMs] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isAnalyzing) {
      const t0 = Date.now();
      setStartTime(t0);
      setElapsedMs(0);
      timerRef.current = setInterval(() => {
        setElapsedMs(Date.now() - t0);
      }, 80);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      if (!isAnalyzing && startTime) {
        setElapsedMs(Date.now() - startTime);
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isAnalyzing]);

  // Don't render if idle and no result/error to show
  if (!isAnalyzing && !result && !error) return null;
  // If result exists and no error, show the completed trace instead (handled below)

  const hasError = Boolean(error && !isAnalyzing);
  const statuses = isAnalyzing ? getStageStatuses(elapsedMs, false) : PIPELINE.map(() => (hasError ? 'pending' : 'done') as StageStatus);
  const activeIdx = statuses.findIndex(s => s === 'active');
  const activeStage = activeIdx >= 0 ? PIPELINE[activeIdx] : null;

  // Real backend trace data if result available
  const traceMap = result?.execution_trace ? mapTraceToStage(result.execution_trace) : {};
  const specialistFromResult = result?.evidence?.[0]?.specialist || null;
  const totalDuration = result?.duration_ms ?? (isAnalyzing ? elapsedMs : null);
  const configFromResult = result?.input?.configuration;
  const intentFromResult = result?.intent?.type;

  // Progress bar: done stages / total
  const doneCount = statuses.filter(s => s === 'done').length;
  const progressPct = isAnalyzing
    ? Math.round((doneCount / PIPELINE.length) * 100)
    : hasError ? 40 : 100;

  if (!isAnalyzing && !hasError) return null; // result rendered elsewhere; only show during analysis

  return (
    <div className={`rounded-xl border backdrop-blur-xl overflow-hidden shadow-xl transition-all duration-300 ${
      hasError
        ? 'bg-rose-950/20 border-rose-500/40'
        : 'bg-slate-950/85 border-cyan-500/30'
    }`}>

      {/* Header Bar */}
      <div className={`flex items-center justify-between px-4 py-2.5 border-b ${
        hasError ? 'border-rose-500/20 bg-rose-950/30' : 'border-cyan-500/20 bg-slate-900/60'
      }`}>
        <div className="flex items-center gap-2.5">
          {hasError ? (
            <div className="w-2 h-2 rounded-full bg-rose-400" />
          ) : (
            <div className="relative w-2 h-2">
              <div className="absolute inset-0 rounded-full bg-cyan-400 animate-ping opacity-70" />
              <div className="w-2 h-2 rounded-full bg-cyan-400" />
            </div>
          )}
          <span className={`font-mono text-[11px] font-bold uppercase tracking-widest ${
            hasError ? 'text-rose-400' : 'text-cyan-300'
          }`}>
            {hasError ? 'ANALYSIS FAILED' : 'ANALYSIS IN PROGRESS'}
          </span>
        </div>

        <div className="flex items-center gap-3 font-mono text-[10px] text-slate-400">
          {isAnalyzing && (
            <span className="tabular-nums text-slate-300">
              {formatDuration(elapsedMs)}
            </span>
          )}
          {activeStage && !hasError && (
            <span className="hidden sm:inline text-cyan-400 font-semibold">
              {activeStage.label}
            </span>
          )}
          {specialistFromResult && (
            <span className="px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/40 text-cyan-300 font-semibold">
              {specialistFromResult}
            </span>
          )}
          {configFromResult && (
            <span className="hidden md:inline px-2 py-0.5 rounded bg-slate-800/80 border border-white/8 text-slate-300">
              {configFromResult.replace(/_/g, ' ')}
            </span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-[2px] bg-slate-800/80 relative overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ease-out ${
            hasError ? 'bg-rose-500' : 'bg-gradient-to-r from-cyan-500 to-cyan-300'
          }`}
          style={{ width: `${progressPct}%` }}
        />
        {isAnalyzing && (
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-[shimmer_1.5s_linear_infinite] w-[200%] -left-full" />
        )}
      </div>

      {/* Pipeline Stage List */}
      <div className="px-4 py-3.5 flex flex-col gap-1.5">
        {PIPELINE.map((stage, idx) => {
          const status = statuses[idx];
          const traceStep = traceMap[stage.id];

          const isDone    = status === 'done';
          const isActive  = status === 'active';
          const isPending = status === 'pending';
          const isErr     = status === 'error';

          const stageDuration = traceStep?.duration_ms
            ? formatDuration(traceStep.duration_ms)
            : isDone && isAnalyzing ? '✓' : null;

          return (
            <div
              key={stage.id}
              className={`flex items-center gap-2.5 py-0.5 transition-all duration-200 ${
                isPending ? 'opacity-30' : 'opacity-100'
              }`}
            >
              {/* Status Node */}
              <div className="shrink-0 w-5 h-5 flex items-center justify-center">
                {isDone ? (
                  <div className="w-4 h-4 rounded-full bg-emerald-950/80 border border-emerald-500/60 flex items-center justify-center">
                    <svg className="w-2.5 h-2.5 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </div>
                ) : isActive ? (
                  <div className="w-4 h-4 rounded-full bg-cyan-950/90 border border-cyan-400/80 ring-2 ring-cyan-400/25 flex items-center justify-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                  </div>
                ) : isErr ? (
                  <div className="w-4 h-4 rounded-full bg-rose-950/80 border border-rose-500/60 flex items-center justify-center">
                    <svg className="w-2.5 h-2.5 text-rose-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </div>
                ) : (
                  <div className="w-4 h-4 rounded-full border border-slate-700/60 bg-slate-900/40" />
                )}
              </div>

              {/* Stage Info */}
              <div className="flex-1 min-w-0 flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className={`font-mono text-[11px] font-bold shrink-0 ${
                    isDone ? 'text-slate-200' : isActive ? 'text-cyan-300' : isErr ? 'text-rose-400' : 'text-slate-500'
                  }`}>
                    {String(idx + 1).padStart(2, '0')} {stage.label}
                  </span>
                  {isActive && (
                    <span className="hidden sm:inline font-mono text-[9.5px] text-slate-500 truncate">
                      — {stage.description}
                    </span>
                  )}
                  {/* Specialist name on the specialist stage */}
                  {stage.id === 'specialist' && isActive && specialistFromResult && (
                    <span className="ml-1 px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/50 text-[9px] font-mono font-bold">
                      {specialistFromResult}
                    </span>
                  )}
                  {/* Intent on intent stage when done */}
                  {stage.id === 'intent' && isDone && intentFromResult && (
                    <span className="ml-1 px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-white/8 text-[9px] font-mono">
                      {intentFromResult}
                    </span>
                  )}
                </div>

                {/* Duration / status tag */}
                <div className="shrink-0 font-mono text-[9.5px] tabular-nums">
                  {stageDuration && (
                    <span className={isDone ? 'text-emerald-500' : 'text-cyan-400'}>
                      {stageDuration}
                    </span>
                  )}
                  {isActive && !stageDuration && (
                    <span className="flex gap-0.5">
                      <span className="w-1 h-1 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1 h-1 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '120ms' }} />
                      <span className="w-1 h-1 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '240ms' }} />
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer status row */}
      <div className={`flex items-center justify-between px-4 py-2 border-t text-[10px] font-mono ${
        hasError
          ? 'border-rose-500/20 bg-rose-950/20 text-rose-400'
          : 'border-white/5 bg-slate-950/40 text-slate-400'
      }`}>
        <div className="flex items-center gap-2">
          {hasError ? (
            <>
              <svg className="w-3 h-3 text-rose-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <span>{error}</span>
            </>
          ) : isAnalyzing ? (
            <>
              <span className="text-slate-500">ELAPSED</span>
              <span className="text-slate-200 tabular-nums">{formatDuration(elapsedMs)}</span>
              <span className="text-slate-600">·</span>
              <span className="text-slate-500">STAGE</span>
              <span className="text-cyan-400">{doneCount + 1} / {PIPELINE.length}</span>
            </>
          ) : null}
        </div>

        {totalDuration && (
          <span className="text-slate-500 tabular-nums">
            {hasError ? 'Failed after' : 'Total'}: {formatDuration(totalDuration)}
          </span>
        )}
      </div>
    </div>
  );
};
