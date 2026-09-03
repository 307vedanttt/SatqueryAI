import React from 'react';
import type { ConfidenceBreakdown, ConfidenceLabel } from '../../types';

interface ConfidenceBadgeProps {
  confidence?: ConfidenceBreakdown | null;
  score?: number;
  label?: ConfidenceLabel;
  showBar?: boolean;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  confidence,
  score,
  label,
  showBar = true,
}) => {
  const finalScore = score ?? confidence?.final_score ?? null;
  const finalLabel = label ?? confidence?.label ?? (
    finalScore !== null
      ? finalScore >= 0.75
        ? 'high'
        : finalScore >= 0.4
        ? 'medium'
        : 'low'
      : 'insufficient'
  );

  if (finalScore === null) {
    return (
      <span className="badge font-mono text-xs bg-surface-2 text-text-3 border border-glass-border">
        Confidence Unavailable
      </span>
    );
  }

  const percent = Math.round(finalScore * 100);

  let labelText = 'HIGH';
  let badgeClass = 'badge-success';

  if (finalLabel === 'medium') {
    labelText = 'MODERATE';
    badgeClass = 'badge-warn';
  } else if (finalLabel === 'low' || finalLabel === 'insufficient') {
    labelText = 'INSUFFICIENT';
    badgeClass = 'badge-error';
  }

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between gap-2">
        <span className={`badge ${badgeClass} font-mono font-bold text-xs`}>
          {labelText} • {percent}%
        </span>
      </div>

      {showBar && (
        <div className="w-full bg-surface-2 h-1.5 rounded-full overflow-hidden border border-glass-border">
          <div
            className={`h-full transition-all duration-300 ${
              finalLabel === 'high'
                ? 'bg-emerald-500'
                : finalLabel === 'medium'
                ? 'bg-amber-500'
                : 'bg-rose-500'
            }`}
            style={{ width: `${percent}%` }}
          />
        </div>
      )}
    </div>
  );
};
