import React from 'react';
import type { InputConfiguration, IntentResult } from '../../types';

interface RoutingSummaryProps {
  intent?: IntentResult | null;
  configuration?: InputConfiguration;
  specialist?: string;
}

export const RoutingSummary: React.FC<RoutingSummaryProps> = ({
  intent,
  configuration = 'SINGLE_OPTICAL',
  specialist = 'vqa',
}) => {
  if (!intent) return null;

  return (
    <div className="routing-summary p-3 bg-surface rounded-xl border border-glass-border my-2">
      <div className="text-[10px] font-mono text-text-3 uppercase tracking-wider mb-2 flex items-center justify-between">
        <span>BOUNDED ORCHESTRATION</span>
        <span className="text-accent text-[11px]">✓ DETERMINISTIC ROUTE</span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs font-mono">
        <div className="p-2 rounded bg-surface-2 border border-glass-border/40">
          <span className="text-[9px] text-text-3 block uppercase">INPUT CONFIG</span>
          <span className="text-text font-bold text-[11px] truncate block" title={configuration}>
            {configuration.replace(/_/g, ' ')}
          </span>
        </div>

        <div className="p-2 rounded bg-surface-2 border border-glass-border/40">
          <span className="text-[9px] text-text-3 block uppercase">QUERY INTENT</span>
          <span className="text-text font-bold text-[11px] truncate block" title={intent.type}>
            {intent.type.replace(/_/g, ' ')}
          </span>
        </div>

        <div className="p-2 rounded bg-surface-2 border border-glass-border/40">
          <span className="text-[9px] text-text-3 block uppercase">SELECTED SPECIALIST</span>
          <span className="text-cyan-400 font-bold text-[11px] truncate block" title={specialist}>
            {specialist.replace(/_/g, ' ').toUpperCase()}
          </span>
        </div>
      </div>
    </div>
  );
};
