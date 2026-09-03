import React from 'react';
import type { AnalysisResponse } from '../types';
import { ConfidenceDisplay } from './ConfidenceDisplay';
import { EvidencePanel } from './EvidencePanel';
import { ExecutionTrace } from './ExecutionTrace';

interface ResultPanelProps {
  result: AnalysisResponse | null;
  isLoading: boolean;
  error: string | null;
}

export const ResultPanel: React.FC<ResultPanelProps> = ({ result, isLoading, error }) => {
  if (isLoading) {
    return (
      <div className="card">
        <div className="card-title">
          <span className="icon">⏳</span>
          <span>Analyzing Remote Sensing Imagery...</span>
        </div>
        <div className="flex flex-col gap-3 py-4">
          <div className="skeleton h-6 w-3/4" />
          <div className="skeleton h-20 w-full" />
          <div className="skeleton h-12 w-full" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-title text-error">
          <span className="icon">⚠️</span>
          <span>Analysis Error</span>
        </div>
        <div className="error-block mt-2">
          <div>{error}</div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="card">
        <div className="empty-state">
          <div className="empty-state-icon">📡</div>
          <div className="empty-state-title">No Analysis Executed Yet</div>
          <div className="empty-state-sub">
            Upload remote sensing imagery and enter a natural language question to start the automated reasoning flow.
          </div>
        </div>
      </div>
    );
  }

  const { answer, confidence, disagreement, execution_trace, evidence, intent, input } = result;

  return (
    <div className="result-panel fade-in">
      <div className="card">
        <div className="flex justify-between items-center mb-2">
          <div className="card-title mb-0">
            <span className="icon">💬</span>
            <span>Analysis Answer</span>
          </div>
          {intent && (
            <div className="intent-chip">
              <span>{input.configuration}</span> • <span>{intent.type}</span>
            </div>
          )}
        </div>

        <div className={`answer-block ${answer.is_refused ? 'answer-refused' : ''}`}>
          <div className="answer-text">{answer.text}</div>
          {answer.is_refused && (
            <div className="text-xs text-warn mt-2">
              Reason: {answer.refusal_reason}
            </div>
          )}
        </div>

        <div className="mt-3">
          <ConfidenceDisplay confidence={confidence} />
        </div>

        {disagreement.detected && (
          <div className="disagreement-banner mt-3">
            <span>⚠️</span>
            <div>
              <strong>Disagreement Detected across Specialists:</strong> {disagreement.explanation}
            </div>
          </div>
        )}
      </div>

      <EvidencePanel evidence={evidence} />
      <ExecutionTrace steps={execution_trace} />
    </div>
  );
};
