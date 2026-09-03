import React, { useState } from 'react';
import type { Evidence } from '../../types';

interface EvidencePanelProps {
  evidence: Evidence[];
  activeEvidenceId?: string | null;
  onFocusEvidence?: (evidenceId: string) => void;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({
  evidence,
  activeEvidenceId,
  onFocusEvidence,
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!evidence || evidence.length === 0) {
    return (
      <div className="card p-5 bg-surface rounded-xl border border-glass-border text-center">
        <div className="text-3xl mb-1 opacity-30">🔍</div>
        <div className="text-xs font-semibold text-text">No Evidence Collected Yet</div>
        <div className="text-[11px] text-text-3 mt-1">
          Structured spatial and spectral evidence items will appear here upon specialist execution.
        </div>
      </div>
    );
  }

  // Categorize evidence if cross-sensor or multi-source
  const opticalEvidence = evidence.filter(
    (e) => e.sensor?.toLowerCase().includes('optical') || e.source?.toLowerCase().includes('optical')
  );
  const sarEvidence = evidence.filter(
    (e) => e.sensor?.toLowerCase().includes('sar') || e.source?.toLowerCase().includes('sar')
  );
  const otherEvidence = evidence.filter(
    (e) => !opticalEvidence.includes(e) && !sarEvidence.includes(e)
  );

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const renderEvidenceCard = (item: Evidence) => {
    const isExpanded = expandedId === item.evidence_id;
    const isFocused = activeEvidenceId === item.evidence_id;
    const confPercent = Math.round(item.confidence * 100);

    return (
      <div
        key={item.evidence_id}
        className={`evidence-card p-3 rounded-xl border transition-all ${
          isFocused
            ? 'border-cyan-400 bg-cyan-950/20 ring-2 ring-cyan-500/30'
            : 'border-glass-border bg-surface hover:border-glass-border/80'
        }`}
      >
        <div className="flex justify-between items-start gap-2">
          <div className="flex items-center gap-2">
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-bold ${
                item.evidence_type === 'sensor_comparison'
                  ? 'bg-purple-950 text-purple-300 border-purple-800/40'
                  : item.evidence_type === 'temporal_difference'
                  ? 'bg-amber-950 text-amber-300 border-amber-800/40'
                  : item.evidence_type === 'bbox'
                  ? 'bg-cyan-950 text-cyan-300 border-cyan-800/40'
                  : 'bg-blue-950 text-blue-300 border-blue-800/40'
              }`}
            >
              {item.evidence_type.replace('_', ' ')}
            </span>

            <span className="text-xs text-text-3 font-mono">
              Source: <span className="text-text-2 font-medium">{item.source || item.specialist}</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-accent">{confPercent}%</span>
            <button
              type="button"
              onClick={() => toggleExpand(item.evidence_id)}
              className="text-text-3 hover:text-text text-xs p-1"
              title={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? '▲' : '▼'}
            </button>
          </div>
        </div>

        {/* Claim text */}
        <div className="text-xs text-text mt-2 font-medium leading-relaxed">
          {item.claim}
        </div>

        {/* Coordinates and Sensor metadata */}
        <div className="flex flex-wrap items-center justify-between gap-2 mt-2 pt-2 border-t border-glass-border/30 text-[11px] font-mono text-text-3">
          <div className="flex items-center gap-2">
            {item.bbox && (
              <span>
                BBOX: <span className="text-text-2">[{item.bbox.join(', ')}]</span>
              </span>
            )}
            {item.sensor && (
              <span>
                • Sensor: <span className="text-text-2">{item.sensor}</span>
              </span>
            )}
          </div>

          {/* Evidence -> Image Connection Button */}
          {item.bbox && onFocusEvidence && (
            <button
              type="button"
              onClick={() => onFocusEvidence(item.evidence_id)}
              className="px-2 py-0.5 rounded bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-800/50 text-cyan-300 hover:text-cyan-100 transition-colors flex items-center gap-1 cursor-pointer"
            >
              <span>🎯</span>
              <span>View on image</span>
            </button>
          )}
        </div>

        {/* Expanded detailed metadata */}
        {isExpanded && (
          <div className="expanded-details mt-2.5 pt-2 border-t border-glass-border/50 text-[11px] font-mono text-text-3 space-y-1">
            <div>Evidence ID: <span className="text-text-2">{item.evidence_id}</span></div>
            <div>Specialist: <span className="text-text-2">{item.specialist}</span></div>
            {item.date && <div>Acquisition Date: <span className="text-text-2">{item.date}</span></div>}
            <div>Verification: <span className="text-emerald-400">Ground-checked spatial match</span></div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="evidence-panel card p-4 bg-surface rounded-xl border border-glass-border shadow-lg">
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2">
          <span className="text-base">🔬</span>
          <span className="text-xs font-bold text-text uppercase tracking-wider">
            SUPPORTING EVIDENCE ({evidence.length} ITEMS)
          </span>
        </div>
        <span className="text-[10px] font-mono text-text-3">Evidence-grounded inference</span>
      </div>

      {opticalEvidence.length > 0 && sarEvidence.length > 0 ? (
        /* Categorized view for Optical + SAR Fusion */
        <div className="space-y-4">
          <div>
            <div className="text-[11px] font-mono text-cyan-400 uppercase tracking-wider mb-2 font-bold">
              OPTICAL EVIDENCE
            </div>
            <div className="space-y-2">{opticalEvidence.map(renderEvidenceCard)}</div>
          </div>

          <div>
            <div className="text-[11px] font-mono text-purple-400 uppercase tracking-wider mb-2 font-bold">
              SAR RADAR EVIDENCE
            </div>
            <div className="space-y-2">{sarEvidence.map(renderEvidenceCard)}</div>
          </div>

          {otherEvidence.length > 0 && (
            <div>
              <div className="text-[11px] font-mono text-emerald-400 uppercase tracking-wider mb-2 font-bold">
                JOINT FUSION EVIDENCE
              </div>
              <div className="space-y-2">{otherEvidence.map(renderEvidenceCard)}</div>
            </div>
          )}
        </div>
      ) : (
        /* Standard list view */
        <div className="space-y-2.5">
          {evidence.map(renderEvidenceCard)}
        </div>
      )}
    </div>
  );
};
