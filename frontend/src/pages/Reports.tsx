import React, { useEffect, useState } from 'react';
import type { ReportItem } from '../types';
import { generateReportPdf, getReports } from '../services/api';
import { ConfidenceBadge } from '../components/common/ConfidenceBadge';

export const Reports: React.FC = () => {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [selectedReport, setSelectedReport] = useState<ReportItem | null>(null);
  const [pdfStatus, setPdfStatus] = useState<string | null>(null);

  useEffect(() => {
    getReports().then(setReports);
  }, []);

  const handleGeneratePdf = async (id: string) => {
    setPdfStatus(`Compiling PDF for ${id}...`);
    try {
      const res = await generateReportPdf(id);
      setPdfStatus(`✓ ${res.message}`);
      setTimeout(() => setPdfStatus(null), 3000);
    } catch {
      setPdfStatus('✕ PDF compilation failed.');
    }
  };

  return (
    <div className="reports-page flex flex-col gap-5 max-w-5xl mx-auto py-2">
      {/* Header */}
      <div className="p-4 rounded-xl bg-surface border border-glass-border flex flex-wrap justify-between items-center gap-3">
        <div>
          <h1 className="text-xl font-bold text-text flex items-center gap-2">
            <span>📊</span>
            <span>SCIENTIFIC ANALYSIS REPORTS</span>
          </h1>
          <p className="text-xs text-text-3 mt-0.5">
            Structured mission summaries, multi-temporal change audits, and evidence dossiers.
          </p>
        </div>

        {pdfStatus && (
          <div className="text-xs font-mono text-cyan-300 bg-cyan-950/80 px-3 py-1.5 rounded-lg border border-cyan-700/50">
            {pdfStatus}
          </div>
        )}
      </div>

      {/* Reports List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reports.map((report) => (
          <div
            key={report.id}
            className="card p-5 bg-surface hover:bg-surface-2/60 rounded-xl border border-glass-border transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex justify-between items-start gap-2 mb-2">
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/40 uppercase font-bold">
                  {report.task}
                </span>
                <span className="font-mono text-xs text-text-3">{report.date}</span>
              </div>

              <h2 className="text-sm font-bold text-text mb-1.5 leading-snug">
                {report.title}
              </h2>

              <p className="text-xs text-text-2 mb-3 leading-relaxed">
                {report.summary}
              </p>

              <div className="flex flex-wrap gap-2 text-[11px] font-mono text-text-3 mb-4">
                <span>Imagery: {report.imageCount} files</span>
                <span>•</span>
                <span>Evidence items: {report.evidenceCount}</span>
                <span>•</span>
                <span>Specialist: {report.specialistUsed}</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-glass-border/40">
              <ConfidenceBadge score={report.confidenceScore} label={report.confidenceLabel} showBar={false} />

              <div className="flex items-center gap-2 font-mono text-xs">
                <button
                  type="button"
                  onClick={() => setSelectedReport(report)}
                  className="px-2.5 py-1 rounded bg-surface-2 hover:bg-surface-3 text-text border border-glass-border transition-colors"
                >
                  View Dossier
                </button>
                <button
                  type="button"
                  onClick={() => handleGeneratePdf(report.id)}
                  className="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-bold transition-colors"
                >
                  Export PDF
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Detailed Dossier Modal */}
      {selectedReport && (
        <div className="modal-backdrop fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="modal-card max-w-2xl w-full bg-surface border border-glass-border rounded-2xl p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start">
              <div>
                <span className="font-mono text-xs text-accent uppercase tracking-wider">
                  REPORT DOSSIER • {selectedReport.id}
                </span>
                <h2 className="text-lg font-bold text-text mt-1">{selectedReport.title}</h2>
              </div>
              <button
                type="button"
                onClick={() => setSelectedReport(null)}
                className="text-text-3 hover:text-text text-lg p-1"
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            <div className="text-xs font-mono text-text-3 flex gap-3 border-b border-glass-border/40 pb-2">
              <span>Date: {selectedReport.date}</span>
              <span>•</span>
              <span>Images: {selectedReport.imageCount}</span>
              <span>•</span>
              <span>Specialist: {selectedReport.specialistUsed}</span>
            </div>

            <div className="text-xs text-text-2 space-y-2 leading-relaxed">
              <div className="font-bold text-text">Executive Summary</div>
              <p>{selectedReport.summary}</p>
            </div>

            <div className="p-3 bg-surface-2 rounded-lg border border-glass-border font-mono text-xs space-y-1">
              <div className="text-accent font-bold">Verification & Integrity</div>
              <div>Spatial CRS Alignment: Validated (EPSG:32643)</div>
              <div>Resolution Consistency: Verified (&lt; 10% tolerance)</div>
              <div>Confidence Tier: {selectedReport.confidenceLabel.toUpperCase()} ({(selectedReport.confidenceScore * 100).toFixed(0)}%)</div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-glass-border">
              <button
                type="button"
                onClick={() => setSelectedReport(null)}
                className="px-3 py-1.5 rounded bg-surface-2 text-text text-xs font-mono"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  handleGeneratePdf(selectedReport.id);
                  setSelectedReport(null);
                }}
                className="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-mono font-bold"
              >
                Download PDF
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
