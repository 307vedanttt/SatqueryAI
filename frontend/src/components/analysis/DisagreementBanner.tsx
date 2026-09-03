import React from 'react';
import type { DisagreementResult } from '../../types';

interface DisagreementBannerProps {
  disagreement?: DisagreementResult | null;
}

export const DisagreementBanner: React.FC<DisagreementBannerProps> = ({ disagreement }) => {
  if (!disagreement?.detected) return null;

  return (
    <div className="disagreement-banner p-3.5 rounded-xl border border-amber-500/40 bg-amber-950/20 text-xs my-3 flex items-start gap-2.5">
      <span className="text-xl leading-none text-amber-400" aria-hidden="true">
        ⚠️
      </span>
      <div className="flex flex-col gap-1">
        <div className="font-bold text-amber-300 uppercase tracking-wide text-[11px] font-mono">
          MODEL DISAGREEMENT DETECTED
        </div>

        <div className="text-text-2 leading-relaxed text-xs">
          {disagreement.explanation ||
            'Specialist outputs are not fully consistent across sensors or models. Confidence has been reduced accordingly.'}
        </div>

        {disagreement.items && disagreement.items.length > 0 && (
          <div className="mt-2 space-y-1 font-mono text-[11px] bg-surface/60 p-2 rounded border border-amber-500/20">
            {disagreement.items.map((item, idx) => (
              <div key={idx} className="flex justify-between items-center text-text-3">
                <span>
                  [{item.source}]: <span className="text-amber-200">"{item.claim}"</span>
                </span>
                <span className="text-[10px] text-amber-400 font-semibold">
                  {(item.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        )}

        <div className="text-[10px] text-amber-400/80 font-mono mt-1">
          Ground verification or expert review recommended for highlighted discordant regions.
        </div>
      </div>
    </div>
  );
};
