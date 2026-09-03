import React from 'react';
import type { AnalysisResponse } from '../../types';
import { ConfidenceBadge } from '../common/ConfidenceBadge';
import { DisagreementBanner } from './DisagreementBanner';

interface EvidenceAndResultsPanelProps {
  result: AnalysisResponse | null;
  isLoading: boolean;
  activeEvidenceId?: string | null;
  onFocusEvidence?: (id: string) => void;
  onClearTrace?: () => void;
}

export const EvidenceAndResultsPanel: React.FC<EvidenceAndResultsPanelProps> = ({
  result,
  isLoading,
  activeEvidenceId,
  onFocusEvidence,
  onClearTrace,
}) => {
  const answer = result?.answer;
  const confidence = result?.confidence;
  const evidence = result?.evidence || [];
  const traceSteps = result?.execution_trace || [];
  const intent = result?.intent;

  const specialistDisplayName =
    intent?.type === 'GROUNDING'
      ? 'RS-Grounding Specialist'
      : intent?.type === 'CHANGE_DESCRIPTION' || intent?.type === 'CHANGE_VQA'
      ? 'Bi-Temporal Change Specialist'
      : intent?.type === 'OPTICAL_SAR_ANALYSIS'
      ? 'Optical-SAR Fusion Specialist'
      : 'RS-VQA Specialist';

  const modelUsed = intent?.required_capabilities?.[0] || 'mock_single_image';

  // Categorize evidence
  const opticalEvidence = evidence.filter(
    (e) => e.sensor?.toLowerCase().includes('optical') || e.source?.toLowerCase().includes('optical')
  );
  const sarEvidence = evidence.filter(
    (e) => e.sensor?.toLowerCase().includes('sar') || e.source?.toLowerCase().includes('sar')
  );
  const otherEvidence = evidence.filter(
    (e) => !opticalEvidence.includes(e) && !sarEvidence.includes(e)
  );

  const confidenceScore = confidence?.final_score ? Math.round(confidence.final_score * 100) : null;

  // Canonical 8-step pipeline timeline
  const pipelineStages = [
    { label: 'Input Validation', key: 'validation' },
    { label: 'Configuration Detection', key: 'config' },
    { label: 'Intent Detection', key: 'intent' },
    { label: 'Specialist Selection', key: 'routing' },
    { label: 'Model Execution', key: 'execution' },
    { label: 'Evidence Synthesis', key: 'synthesis' },
    { label: 'Confidence Calculation', key: 'confidence' },
    { label: 'Result Ready', key: 'ready' },
  ];

  return (
    <aside className="evidence-results-panel flex flex-col gap-4 w-full">
      {/* Top Header */}
      <div className="flex items-center justify-between px-1">
        <h3 className="font-mono text-xs font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-1.5">
          <span className="text-cyan-400">📊</span>
          <span>AI RESULTS & EVIDENCE</span>
        </h3>
        {result ? (
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/70 border border-emerald-700/50 px-2 py-0.5 rounded font-bold shadow-[0_0_8px_rgba(16,185,129,0.3)]">
            ● READY
          </span>
        ) : (
          <span className="text-[10px] font-mono text-slate-500 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
            ● STANDBY
          </span>
        )}
      </div>

      {/* 1. Confidence & Specialist Card */}
      <div className="card p-4 bg-[#0a101d] rounded-xl border border-slate-800 shadow-sm flex flex-col gap-3">
        <div className="flex justify-between items-center">
          <span className="text-[10px] font-mono uppercase font-bold text-slate-400 tracking-wider">
            CONFIDENCE SCORE
          </span>
          {confidence && <ConfidenceBadge confidence={confidence} />}
        </div>

        {/* Big Arc / Gauge Display */}
        <div className="flex items-center gap-4 py-1">
          <div className="w-16 h-16 rounded-full border-4 border-slate-800 border-t-cyan-400 flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(6,182,212,0.2)]">
            <span className="font-mono text-base font-extrabold text-white">
              {confidenceScore !== null ? `${confidenceScore}%` : '-- %'}
            </span>
          </div>

          <div className="flex-1 min-w-0">
            <div className="text-xs font-bold text-slate-100 truncate">
              {result ? specialistDisplayName : 'RS Specialist Standby'}
            </div>
            <div className="text-[10.5px] font-mono text-slate-400 mt-0.5 truncate">
              Model: <span className="text-cyan-400">{result ? modelUsed : 'Deterministic Router'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Grounded Answer Card */}
      <div className="card p-4 bg-[#0a101d] rounded-xl border border-slate-800 shadow-sm flex flex-col gap-2.5">
        <div className="flex justify-between items-center">
          <h4 className="font-mono text-xs font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-1.5">
            <span className="text-cyan-400">💡</span>
            <span>GROUNDED ANSWER</span>
          </h4>
          {result?.duration_ms && (
            <span className="text-[10px] font-mono text-slate-500">
              {result.duration_ms} ms
            </span>
          )}
        </div>

        {isLoading ? (
          <div className="p-4 rounded-lg bg-[#070d18] border border-slate-800/80 flex flex-col gap-2.5 animate-pulse">
            <div className="flex items-center gap-2 text-xs text-cyan-400 font-mono">
              <span className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
              <span>Synthesizing grounded response...</span>
            </div>
            <div className="h-3 w-full bg-slate-800 rounded" />
            <div className="h-3 w-4/5 bg-slate-800 rounded" />
            <div className="h-3 w-3/5 bg-slate-800 rounded" />
          </div>
        ) : !result ? (
          <div className="p-5 rounded-lg bg-[#070d18] border border-slate-800/80 text-center font-sans text-xs text-slate-400 leading-relaxed">
            <div className="text-2xl mb-1.5 opacity-30">📡</div>
            <div className="font-bold text-slate-200">No analysis yet</div>
            <div className="text-[11px] text-slate-500 mt-1">
              Upload imagery and run an analysis to see grounded results.
            </div>
          </div>
        ) : (
          <div className="p-3.5 rounded-lg bg-[#070d18] border border-slate-800/80 flex flex-col gap-2">
            <p className="text-xs sm:text-[13px] text-slate-200 leading-relaxed whitespace-pre-line font-sans">
              {answer?.text}
            </p>

            {answer?.is_refused && (
              <div className="mt-2 p-2.5 rounded bg-amber-950/40 border border-amber-500/30 text-xs text-amber-200">
                <strong>Fail-safe Notice:</strong> {answer.refusal_reason || 'Insufficient evidence.'}
              </div>
            )}

            {result.disagreement && <DisagreementBanner disagreement={result.disagreement} />}

            {confidence?.explanation && (
              <div className="mt-2 pt-2 border-t border-slate-800/80 text-[10.5px] font-mono text-slate-400 flex items-start gap-1.5">
                <span className="text-cyan-400 font-bold">ℹ</span>
                <span>{confidence.explanation}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 3. Evidence Summary Card */}
      <div className="card p-4 bg-[#0a101d] rounded-xl border border-slate-800 shadow-sm flex flex-col gap-2.5">
        <div className="flex justify-between items-center">
          <h4 className="font-mono text-xs font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-1.5">
            <span className="text-cyan-400">🔬</span>
            <span>EVIDENCE SUMMARY</span>
          </h4>
          {evidence.length > 0 && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-cyan-300 border border-blue-800/60 font-semibold">
              {evidence.length} ITEMS
            </span>
          )}
        </div>

        {evidence.length === 0 ? (
          <div className="p-4 rounded-lg bg-[#070d18] border border-slate-800/80 text-center font-sans text-xs text-slate-400 leading-relaxed">
            <div className="font-semibold text-slate-300">No evidence available.</div>
            <div className="text-[11px] text-slate-500 mt-1">
              Results and supporting evidence will appear here after analysis.
            </div>
          </div>
        ) : opticalEvidence.length > 0 && sarEvidence.length > 0 ? (
          <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider">
                Optical Observations:
              </span>
              {opticalEvidence.map((item, idx) => (
                <div key={idx} className="p-2 rounded bg-[#070d18] border border-slate-800 text-[11px] font-sans text-slate-200">
                  {item.claim}
                </div>
              ))}
            </div>

            <div className="flex flex-col gap-1.5 pt-2 border-t border-slate-800/60">
              <span className="text-[10px] font-mono font-bold text-purple-400 uppercase tracking-wider">
                SAR Observations:
              </span>
              {sarEvidence.map((item, idx) => (
                <div key={idx} className="p-2 rounded bg-[#070d18] border border-slate-800 text-[11px] font-sans text-slate-200">
                  {item.claim}
                </div>
              ))}
            </div>

            {otherEvidence.length > 0 && (
              <div className="flex flex-col gap-1.5 pt-2 border-t border-slate-800/60">
                <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-wider">
                  Combined Interpretation:
                </span>
                {otherEvidence.map((item, idx) => (
                  <div key={idx} className="p-2 rounded bg-[#070d18] border border-slate-800 text-[11px] font-sans text-slate-200">
                    {item.claim}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-2.5 max-h-[280px] overflow-y-auto pr-1">
            {evidence.map((item, idx) => {
              const isFocused = activeEvidenceId === item.evidence_id;

              return (
                <div
                  key={item.evidence_id || idx}
                  className={`p-2.5 rounded-lg border transition-all ${
                    isFocused
                      ? 'bg-cyan-950/20 border-cyan-400 ring-1 ring-cyan-500/40'
                      : 'bg-[#070d18] border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex justify-between items-start gap-2">
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800 text-cyan-400 font-bold uppercase">
                      {item.evidence_type.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] font-mono font-bold text-slate-300">
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-200 font-sans mt-1.5 leading-snug">
                    {item.claim}
                  </p>

                  <div className="flex justify-between items-center mt-2 pt-1.5 border-t border-slate-800/60 text-[10px] font-mono text-slate-400">
                    <span>
                      {item.bbox ? `BBOX: [${item.bbox.join(', ')}] px` : item.sensor || 'Spectral Match'}
                    </span>

                    {item.bbox && onFocusEvidence && (
                      <button
                        type="button"
                        onClick={() => onFocusEvidence(item.evidence_id)}
                        className="text-cyan-400 hover:text-cyan-300 hover:underline cursor-pointer flex items-center gap-1"
                      >
                        <span>🎯 View on image</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 4. Execution Trace Timeline */}
      <div className="card p-4 bg-[#0a101d] rounded-xl border border-slate-800 shadow-sm flex flex-col gap-2.5">
        <div className="flex justify-between items-center">
          <h4 className="font-mono text-xs font-extrabold text-slate-100 uppercase tracking-wider flex items-center gap-1.5">
            <span className="text-cyan-400">📋</span>
            <span>EXECUTION TRACE</span>
          </h4>

          {traceSteps.length > 0 && onClearTrace && (
            <button
              type="button"
              onClick={onClearTrace}
              className="text-[10px] font-mono text-slate-500 hover:text-red-400 cursor-pointer"
            >
              Clear
            </button>
          )}
        </div>

        {/* 8-Stage Timeline */}
        <div className="space-y-1.5 font-mono text-xs pt-1">
          {pipelineStages.map((stage, idx) => {
            const hasRun = Boolean(result);
            const isRunning = isLoading && idx <= 4;
            const isCompleted = hasRun;

            return (
              <div
                key={idx}
                className={`flex items-center gap-2 py-0.5 transition-colors ${
                  isCompleted
                    ? 'text-emerald-400 font-semibold'
                    : isRunning
                    ? 'text-cyan-300 font-bold animate-pulse'
                    : 'text-slate-600'
                }`}
              >
                <span className="w-3.5 text-center text-[11px]">
                  {isCompleted ? '✓' : isRunning ? '●' : '○'}
                </span>
                <span className="text-[11px] capitalize">{stage.label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
};
