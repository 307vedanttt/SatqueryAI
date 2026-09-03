import React from 'react';
import type { AnalysisResponse } from '../../types';

interface WorkflowSidebarProps {
  hasFiles: boolean;
  hasQuery: boolean;
  isAnalyzing: boolean;
  result: AnalysisResponse | null;
}

export const WorkflowSidebar: React.FC<WorkflowSidebarProps> = ({
  hasFiles,
  hasQuery,
  isAnalyzing,
  result,
}) => {
  // Determine current active step (1 to 5)
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
      desc: 'Upload satellite or aerial imagery',
      isCompleted: hasFiles,
      isActive: currentStep === 1,
    },
    {
      num: '02',
      title: 'Select Configuration',
      desc: 'Choose analysis configuration',
      isCompleted: hasFiles,
      isActive: currentStep === 2,
    },
    {
      num: '03',
      title: 'Ask Question',
      desc: 'Enter natural language query',
      isCompleted: Boolean(hasQuery && hasFiles),
      isActive: currentStep === 3,
    },
    {
      num: '04',
      title: 'Run Specialist',
      desc: 'AI specialist executes analysis',
      isCompleted: Boolean(result),
      isActive: isAnalyzing || currentStep === 4,
      isLoading: isAnalyzing,
    },
    {
      num: '05',
      title: 'Evidence Result',
      desc: 'Review evidence and confidence',
      isCompleted: Boolean(result),
      isActive: currentStep === 5,
    },
  ];

  return (
    <aside className="workflow-sidebar flex flex-col justify-between w-full h-full min-h-[580px] p-4 bg-[#0a101d] rounded-xl border border-slate-800 shadow-sm">
      <div>
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800/80">
          <span className="text-cyan-400 text-sm">🧭</span>
          <h3 className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider">
            Analysis Workflow
          </h3>
        </div>

        {/* Stepper Timeline */}
        <div className="relative flex flex-col gap-6 pl-1">
          {/* Vertical Connecting Guide Line */}
          <div className="absolute left-[17px] top-4 bottom-6 w-[2px] bg-slate-800 -z-0" />

          {steps.map((s, idx) => {
            return (
              <div key={idx} className="relative z-10 flex items-start gap-3">
                {/* Step Node Circle */}
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-mono font-bold shrink-0 transition-all border ${
                    s.isCompleted
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-600/60 shadow-[0_0_8px_rgba(16,185,129,0.2)]'
                      : s.isLoading
                      ? 'bg-blue-900 text-cyan-300 border-cyan-400 animate-pulse'
                      : s.isActive
                      ? 'bg-blue-600 text-white border-blue-400 shadow-sm shadow-blue-500/30'
                      : 'bg-slate-900 text-slate-500 border-slate-800'
                  }`}
                >
                  {s.isCompleted ? '✓' : s.num}
                </div>

                {/* Step Details */}
                <div className="flex-1 min-w-0 pt-0.5">
                  <div
                    className={`text-xs font-semibold tracking-tight transition-colors ${
                      s.isActive
                        ? 'text-white'
                        : s.isCompleted
                        ? 'text-slate-200'
                        : 'text-slate-400'
                    }`}
                  >
                    {s.title}
                  </div>
                  <div className="text-[10px] text-slate-400 font-sans leading-relaxed mt-0.5">
                    {s.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tip Card at Bottom */}
      <div className="tip-card mt-6 p-3 rounded-lg bg-[#0e1628] border border-slate-800/80 text-[11px] font-sans text-slate-300">
        <div className="flex items-center gap-1.5 font-bold text-cyan-400 mb-1 font-mono text-[10px] uppercase">
          <span>💡</span>
          <span>Analysis Tip</span>
        </div>
        <p className="text-slate-400 text-[10.5px] leading-relaxed">
          Use high-resolution imagery (10m or finer GSD) for more accurate feature grounding and reliable change detection.
        </p>
      </div>
    </aside>
  );
};
