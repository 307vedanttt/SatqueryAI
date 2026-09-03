import React from 'react';
import type { Evidence } from '../types';

interface EvidencePanelProps {
  evidence: Evidence[];
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidence }) => {
  if (!evidence || evidence.length === 0) return null;

  return (
    <div className="card mt-3">
      <div className="card-title">
        <span className="icon">🔍</span>
        <span>Extracted Evidence</span>
      </div>

      <div className="evidence-list">
        {evidence.map((item) => (
          <div key={item.evidence_id} className="evidence-item">
            <span className={`evidence-type-badge type-${item.evidence_type}`}>
              {item.evidence_type.replace('_', ' ')}
            </span>
            <div className="evidence-claim">
              <div>{item.claim}</div>
              {item.bbox && (
                <div className="text-xs font-mono text-text-3 mt-1">
                  BBOX: [{item.bbox.join(', ')}]
                </div>
              )}
            </div>
            <div className="evidence-conf">{(item.confidence * 100).toFixed(0)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
};
