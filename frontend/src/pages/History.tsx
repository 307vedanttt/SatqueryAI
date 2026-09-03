import React, { useEffect, useState } from 'react';
import type { HistoryItem } from '../types';
import { getHistory } from '../services/api';
import { ConfidenceBadge } from '../components/common/ConfidenceBadge';

interface HistoryProps {
  onOpenItem?: (item: HistoryItem) => void;
}

export const History: React.FC<HistoryProps> = ({ onOpenItem }) => {
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [filterText, setFilterText] = useState('');
  const [filterConfig, setFilterConfig] = useState<string>('ALL');

  useEffect(() => {
    getHistory().then(setHistoryItems);
  }, []);

  const filtered = historyItems.filter((item) => {
    const matchesText =
      item.query.toLowerCase().includes(filterText.toLowerCase()) ||
      item.task.toLowerCase().includes(filterText.toLowerCase()) ||
      item.answerSummary.toLowerCase().includes(filterText.toLowerCase());

    const matchesConfig =
      filterConfig === 'ALL' || item.configuration === filterConfig;

    return matchesText && matchesConfig;
  });

  return (
    <div className="history-page flex flex-col gap-5 max-w-5xl mx-auto py-2">
      {/* Header & Filter Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-surface border border-glass-border">
        <div>
          <h1 className="text-xl font-bold text-text flex items-center gap-2">
            <span>📜</span>
            <span>ANALYSIS HISTORY</span>
          </h1>
          <p className="text-xs text-text-3 mt-0.5">
            Audit log of prior remote-sensing specialist executions and groundings.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <input
            type="text"
            placeholder="Search queries..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-surface-2 border border-glass-border text-text placeholder:text-text-3 focus:outline-none focus:border-blue-500 text-xs"
          />

          <select
            value={filterConfig}
            onChange={(e) => setFilterConfig(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-surface-2 border border-glass-border text-text text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Configurations</option>
            <option value="SINGLE_OPTICAL">Single Optical</option>
            <option value="OPTICAL_SAR_PAIR">Optical + SAR</option>
            <option value="BI_TEMPORAL">Bi-Temporal</option>
          </select>
        </div>
      </div>

      {/* History Items List */}
      {filtered.length === 0 ? (
        <div className="card p-8 bg-surface rounded-xl border border-glass-border text-center">
          <div className="text-3xl mb-2 opacity-30">📭</div>
          <div className="text-sm font-semibold text-text">No Analyses Found</div>
          <div className="text-xs text-text-3 mt-1">
            {filterText || filterConfig !== 'ALL'
              ? 'Try relaxing your search query or configuration filter.'
              : 'Execute an analysis in the Workspace to populate this historical audit trail.'}
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map((item) => (
            <div
              key={item.id}
              className="card p-4 bg-surface hover:bg-surface-2/70 rounded-xl border border-glass-border transition-all flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
            >
              <div className="flex flex-col gap-1.5 flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/40 font-bold uppercase">
                    {item.task}
                  </span>
                  <span className="font-mono text-[11px] text-text-3">
                    {new Date(item.timestamp).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>

                <div className="font-bold text-sm text-text truncate" title={item.query}>
                  "{item.query}"
                </div>

                <div className="text-xs text-text-2 line-clamp-2">
                  {item.answerSummary}
                </div>

                <div className="flex items-center gap-3 text-[11px] font-mono text-text-3 mt-1">
                  <span>Files: {item.files.join(', ')}</span>
                  <span>•</span>
                  <span>Config: {item.configuration}</span>
                </div>
              </div>

              <div className="flex sm:flex-col items-end gap-2 shrink-0">
                <ConfidenceBadge score={item.confidenceScore} label={item.confidenceLabel} showBar={false} />

                {onOpenItem && (
                  <button
                    type="button"
                    onClick={() => onOpenItem(item)}
                    className="px-3 py-1 rounded bg-surface-2 hover:bg-blue-600 hover:text-white border border-glass-border text-xs font-mono transition-colors"
                  >
                    Open in Workspace ↗
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
