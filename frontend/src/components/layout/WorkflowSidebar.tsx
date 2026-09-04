import React from 'react';
import type { AnalysisResponse } from '../../types';

interface WorkflowSidebarProps {
  hasFiles: boolean;
  hasQuery: boolean;
  isAnalyzing: boolean;
  result: AnalysisResponse | null;
  error?: string | null;
}

export const WorkflowSidebar: React.FC<WorkflowSidebarProps> = ({
  hasFiles,
  hasQuery,
  isAnalyzing,
  result,
  error,
}) => {
  // Determine current active step index (1 to 5)
  let currentStep = 1;
  if (result) {
    currentStep = 5;
  } else if (isAnalyzing) {
    currentStep = 4;
  } else if (hasFiles && hasQuery) {
    currentStep = 4;
  } else if (hasFiles) {
    currentStep = 3;
  }

  const steps = [
    {
      num: '01',
      title: 'Upload Imagery',
      desc: 'Upload optical or SAR satellite rasters',
      isCompleted: hasFiles,
      isActive: currentStep === 1 && !hasFiles,
      isError: false,
      icon: (
        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
      ),
    },
    {
      num: '02',
      title: 'Select Configuration',
      desc: 'Choose single, cross-modal, or bi-temporal mode',
      isCompleted: hasFiles,
      isActive: currentStep === 2,
      isError: false,
      icon: (
        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <line x1="4" y1="21" x2="4" y2="14" />
          <line x1="4" y1="10" x2="4" y2="3" />
          <line x1="12" y1="21" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12" y2="3" />
          <line x1="20" y1="21" x2="20" y2="16" />
          <line x1="20" y1="12" x2="20" y2="3" />
          <line x1="1" y1="14" x2="7" y2="14" />
          <line x1="9" y1="8" x2="15" y2="8" />
          <line x1="17" y1="16" x2="23" y2="16" />
        </svg>
      ),
    },
    {
      num: '03',
      title: 'Ask Question',
      desc: 'Formulate natural-language query',
      isCompleted: Boolean(hasQuery && hasFiles),
      isActive: currentStep === 3,
      isError: false,
      icon: (
        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      ),
    },
    {
      num: '04',
      title: 'Run Specialist',
      desc: 'Execute bounded execution graph',
      isCompleted: Boolean(result),
      isActive: isAnalyzing || currentStep === 4,
      isError: Boolean(error && !result),
      icon: (
        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <rect x="4" y="4" width="16" height="16" rx="2" ry="2" />
          <rect x="9" y="9" width="6" height="6" />
          <line x1="9" y1="1" x2="9" y2="4" />
          <line x1="15" y1="1" x2="15" y2="4" />
          <line x1="9" y1="20" x2="9" y2="23" />
          <line x1="15" y1="20" x2="15" y2="23" />
          <line x1="20" y1="9" x2="23" y2="9" />
          <line x1="20" y1="15" x2="23" y2="15" />
          <line x1="1" y1="9" x2="4" y2="9" />
          <line x1="1" y1="15" x2="4" y2="15" />
        </svg>
      ),
    },
    {
      num: '05',
      title: 'Evidence Result',
      desc: 'Synthesize grounded evidence & confidence',
      isCompleted: Boolean(result),
      isActive: currentStep === 5,
      isError: false,
      icon: (
        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <polyline points="9 12 11 14 15 10" />
        </svg>
      ),
    },
  ];

  return (
    <aside className="workflow-sidebar flex flex-col justify-between w-full h-full min-h-[520px] p-4 bg-slate-950/75 backdrop-blur-xl rounded-xl border border-white/10 shadow-xl shadow-black/40">
      <div>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <span className="text-cyan-400 font-sans">🧭</span>
            <h3 className="font-mono text-xs font-bold text-slate-100 uppercase tracking-wider">
              INTELLIGENCE WORKFLOW
            </h3>
          </div>
          <span className="text-[10px] font-mono text-cyan-400 px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/40">
            5 STEPS
          </span>
        </div>

        {/* Stepper Timeline */}
        <div className="relative flex flex-col gap-3">
          {steps.map((s, idx) => {
            const isCompleted = s.isCompleted;
            const isActive = s.isActive;
            const isError = s.isError;

            return (
              <div key={idx} className="relative flex items-start gap-3 group">
                {/* Left Column: Number Node & Connecting Line */}
                <div className="flex flex-col items-center shrink-0">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono font-black text-xs tracking-wider border transition-all duration-200 z-10 select-none ${
                      isError
                        ? 'bg-rose-950/80 text-rose-300 border-rose-500/60 shadow-md shadow-rose-950/50'
                        : isCompleted
                        ? 'bg-emerald-950/80 text-emerald-400 border-emerald-500/60 shadow-md shadow-emerald-950/50'
                        : isActive
                        ? 'bg-cyan-950/90 text-cyan-300 border-cyan-400/80 shadow-md shadow-cyan-950/60 ring-1 ring-cyan-400/40'
                        : 'bg-slate-900/60 text-slate-500 border-white/10'
                    }`}
                  >
                    {isError ? (
                      <svg className="w-3.5 h-3.5 text-rose-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                        <line x1="12" y1="9" x2="12" y2="13" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                      </svg>
                    ) : isCompleted ? (
                      <svg className="w-3.5 h-3.5 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : (
                      <span>{s.num}</span>
                    )}
                  </div>

                  {/* Connecting Line Segment */}
                  {idx < steps.length - 1 && (
                    <div
                      className={`w-[2px] h-6 my-1 transition-colors duration-200 ${
                        isCompleted
                          ? 'bg-emerald-500/50'
                          : isActive
                          ? 'bg-gradient-to-b from-cyan-400/60 to-slate-800'
                          : 'bg-slate-800/80'
                      }`}
                    />
                  )}
                </div>

                {/* Right Column: Content Card */}
                <div
                  className={`flex-1 min-w-0 p-2.5 rounded-lg border transition-all duration-150 ${
                    isError
                      ? 'bg-rose-950/20 border-rose-800/40 text-rose-200'
                      : isCompleted
                      ? 'bg-slate-900/40 border-white/5 text-slate-200'
                      : isActive
                      ? 'bg-slate-900/80 border-cyan-500/40 text-white shadow-sm shadow-cyan-950/30'
                      : 'bg-slate-950/40 border-transparent text-slate-500'
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-0.5">
                    <div className="flex items-center gap-1.5 font-bold text-xs tracking-tight">
                      <span className={isActive ? 'text-cyan-400' : isCompleted ? 'text-emerald-400' : 'text-slate-500'}>
                        {s.icon}
                      </span>
                      <span className={isActive ? 'text-white font-semibold' : isCompleted ? 'text-slate-200' : 'text-slate-400'}>
                        {s.title}
                      </span>
                    </div>

                    <span
                      className={`font-mono text-[9px] font-bold px-1.5 py-0.2 rounded border uppercase tracking-wider ${
                        isError
                          ? 'bg-rose-950 text-rose-400 border-rose-800/60'
                          : isCompleted
                          ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60'
                          : isActive
                          ? 'bg-cyan-950 text-cyan-300 border-cyan-800/60'
                          : 'bg-slate-900 text-slate-600 border-slate-800'
                      }`}
                    >
                      {isError ? 'ERROR' : isCompleted ? 'DONE' : isActive ? 'ACTIVE' : 'PENDING'}
                    </span>
                  </div>

                  <p className={`text-[11px] font-sans leading-snug ${
                    isActive ? 'text-slate-300' : isCompleted ? 'text-slate-400' : 'text-slate-500'
                  }`}>
                    {s.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Pipeline Info Card at Bottom */}
      <div className="tip-card mt-4 p-3 rounded-lg bg-slate-950/60 border border-white/10 text-[11px] font-sans text-slate-400 shadow-sm">
        <div className="flex items-center gap-1.5 font-bold text-cyan-400 mb-1 font-mono text-[10px] uppercase tracking-wide">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
          <span>PIPELINE ENGINE</span>
        </div>
        <p className="text-[10.5px] text-slate-400 leading-snug font-sans">
          SatQuery AI automatically classifies input configuration and routes queries to registered specialist tools.
        </p>
      </div>
    </aside>
  );
};

