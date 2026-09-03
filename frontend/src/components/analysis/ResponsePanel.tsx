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
      <div className="card p-5 bg-surface rounded-xl border border-glass-border">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">⏳</span>
          <span className="font-semibold text-sm text-text">Synthesizing Answer...</span>
        </div>
        <div className="space-y-3">
          <div className="skeleton h-5 w-3/4 rounded" />
          <div className="skeleton h-16 w-full rounded" />
          <div className="skeleton h-8 w-1/2 rounded" />
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="card p-6 bg-surface rounded-xl border border-glass-border text-center">
        <div className="text-4xl mb-2 opacity-30">📡</div>
        <div className="text-sm font-semibold text-text">Awaiting Analysis Query</div>
        <div className="text-xs text-text-3 mt-1 max-w-xs mx-auto">
          Enter a question above and click "Analyze" to trigger the bounded remote-sensing specialist pipeline.
        </div>
      </div>
    );
  }

  const { answer, confidence, disagreement, intent, input } = result;
  const isRefused = answer.is_refused || confidence?.label === 'insufficient';

  return (
    <div className="response-panel flex flex-col gap-3">
      {/* Orchestration route */}
      <RoutingSummary
        intent={intent}
        configuration={input.configuration}
        specialist={intent?.required_capabilities?.[0] || 'Vision Specialist'}
      />

      {/* Answer Block */}
      <div
        className={`card p-4 rounded-xl border ${
          isRefused
            ? 'border-amber-500/40 bg-amber-950/15'
            : 'border-glass-border bg-surface shadow-xl'
        }`}
      >
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">💬</span>
            <span className="text-sm font-bold tracking-wide text-text uppercase">
              {isRefused ? 'INSUFFICIENT EVIDENCE' : 'AI ANALYSIS ANSWER'}
            </span>
          </div>

          <ConfidenceBadge confidence={confidence} />
        </div>

        {/* Answer Text */}
        <div className="text-xs sm:text-sm text-text-2 leading-relaxed space-y-2 whitespace-pre-line">
          {answer.text}
        </div>

        {/* Refusal / Fail-Safe Notice */}
        {isRefused && (
          <div className="mt-3 p-3 rounded-lg bg-amber-950/40 border border-amber-500/30 text-xs text-amber-200">
            <strong>Fail-safe Notice:</strong>{' '}
            {answer.refusal_reason ||
              'I cannot reliably answer this query with high confidence from the available imagery. Try asking a question that can be directly supported by the provided sensor data.'}
          </div>
        )}

        {/* Disagreement Notice */}
        <DisagreementBanner disagreement={disagreement} />

        {/* Confidence Explanation */}
        {confidence?.explanation && (
          <div className="mt-3 pt-3 border-t border-glass-border/40 flex items-start gap-2 text-[11px] text-text-3 font-mono">
            <span className="text-accent">ℹ</span>
            <span>{confidence.explanation}</span>
          </div>
        )}
      </div>
    </div>
  );
};
