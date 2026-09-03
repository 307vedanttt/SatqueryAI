import React from 'react';
import type { AnalysisResponse } from '../../types';
import { ConfidenceBadge } from '../common/ConfidenceBadge';
import { DisagreementBanner } from './DisagreementBanner';
import { RoutingSummary } from './RoutingSummary';

interface ResponsePanelProps {
  result: AnalysisResponse | null;
  isLoading: boolean;
}

export const ResponsePanel: React.FC<ResponsePanelProps> = ({ result, isLoading }) => {
  if (isLoading) {
    return (
      <div className="card p-5 bg-[#0d1424] rounded-xl border border-slate-800 shadow-sm animate-pulse">
        <div className="flex items-center gap-2 mb-3">
          <span className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
          <span className="font-semibold text-sm text-slate-200">Synthesizing Answer from Sensor Evidence...</span>
        </div>
        <div className="space-y-2.5">
          <div className="skeleton h-4 w-3/4 rounded bg-slate-800" />
          <div className="skeleton h-14 w-full rounded bg-slate-800" />
          <div className="skeleton h-6 w-1/2 rounded bg-slate-800" />
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="card p-6 bg-[#0d1424] rounded-xl border border-slate-800 text-center shadow-sm">
        <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-xl text-slate-500 mx-auto mb-2.5">
          📡
        </div>
        <div className="text-sm font-semibold text-slate-200">Awaiting Analysis Query</div>
        <div className="text-xs text-slate-400 mt-1 max-w-xs mx-auto leading-relaxed font-sans">
          Enter a question above and click "Analyze" to execute the bounded specialist pipeline.
        </div>
      </div>
    );
  }

  const { answer, confidence, disagreement, intent, input } = result;
  const isRefused = answer.is_refused || confidence?.label === 'insufficient';

  return (
    <div className="response-panel flex flex-col gap-3">
      {/* Specialist & Pipeline Route */}
      <RoutingSummary
        intent={intent}
        configuration={input.configuration}
        specialist={intent?.required_capabilities?.[0] || 'Vision Specialist'}
      />

      {/* Answer Block */}
      <div
        className={`card p-4.5 rounded-xl border transition-all ${
          isRefused
            ? 'border-amber-500/40 bg-[#1f170b] shadow-sm'
            : 'border-slate-800 bg-[#0d1424] shadow-md'
        }`}
      >
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center gap-2">
            <span className="text-base text-cyan-400">💡</span>
            <span className="text-xs font-bold tracking-wider text-slate-200 uppercase font-mono">
              {isRefused ? 'INSUFFICIENT EVIDENCE' : 'AI ANALYSIS ANSWER'}
            </span>
          </div>

          <ConfidenceBadge confidence={confidence} />
        </div>

        {/* Answer Text */}
        <div className="text-xs sm:text-sm text-slate-200 leading-relaxed whitespace-pre-line font-sans">
          {answer.text}
        </div>

        {/* Refusal Notice */}
        {isRefused && (
          <div className="mt-3 p-3 rounded-lg bg-amber-950/40 border border-amber-500/30 text-xs text-amber-200 font-sans">
            <strong>Fail-safe Notice:</strong>{' '}
            {answer.refusal_reason ||
              'Cannot reliably answer this query with high confidence from the available imagery. Try asking a question directly observable in the sensor data.'}
          </div>
        )}

        {/* Sensor Disagreement */}
        <DisagreementBanner disagreement={disagreement} />

        {/* Confidence Explanation */}
        {confidence?.explanation && (
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-start gap-2 text-[11px] text-slate-400 font-mono">
            <span className="text-cyan-400 font-bold">ℹ</span>
            <span>{confidence.explanation}</span>
          </div>
        )}
      </div>
    </div>
  );
};
