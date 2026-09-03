import React from 'react';
import type { ConfidenceBreakdown } from '../types';

interface ConfidenceDisplayProps {
  confidence: ConfidenceBreakdown | null;
}

export const ConfidenceDisplay: React.FC<ConfidenceDisplayProps> = ({ confidence }) => {
  if (!confidence) return null;

  const scorePct = Math.round(confidence.final_score * 100);
  const labelClass = confidence.label;

  return (
    <div className="confidence-block">
      <div className={`confidence-score ${labelClass}`}>{scorePct}%</div>
      <div className="confidence-bar-wrap">
        <div className="flex justify-between items-center">
          <span className="confidence-label">Confidence: {confidence.label}</span>
          <span className="text-xs font-mono text-text-3">Score {confidence.final_score.toFixed(2)}</span>
        </div>
        <div className="confidence-bar">
          <div className={`confidence-fill ${labelClass}`} style={{ width: `${scorePct}%` }} />
        </div>
        <div className="confidence-explanation">{confidence.explanation}</div>
      </div>
    </div>
  );
};
