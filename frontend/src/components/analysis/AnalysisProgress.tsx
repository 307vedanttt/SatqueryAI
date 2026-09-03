import React, { useEffect, useState } from 'react';

interface AnalysisProgressProps {
  isAnalyzing: boolean;
}

export const AnalysisProgress: React.FC<AnalysisProgressProps> = ({ isAnalyzing }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    'Input validation & CRS check',
    'Configuration & modality classification',
    'Query understanding & intent routing',
    'Selecting bounded specialist model',
    'Running remote-sensing inference',
    'Extracting spatial evidence & confidence',
    'Synthesizing grounded response',
  ];

  useEffect(() => {
    if (!isAnalyzing) {
      setCurrentStep(0);
      return;
    }

    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 280);

    return () => clearInterval(interval);
  }, [isAnalyzing]);

  if (!isAnalyzing) return null;

  return (
    <div className="card p-3.5 bg-surface rounded-xl border border-blue-500/30 shadow-lg animate-fade-in my-3">
      <div className="flex items-center gap-2 mb-2.5">
        <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
        <span className="text-xs font-mono font-bold text-blue-400 uppercase tracking-wider">
          ANALYZING IMAGERY & REASONING...
        </span>
      </div>

      <div className="space-y-1.5 font-mono text-xs">
        {steps.map((step, idx) => {
          const isDone = idx < currentStep;
          const isCurrent = idx === currentStep;

          return (
            <div
              key={idx}
              className={`flex items-center gap-2 transition-opacity duration-150 ${
                isDone
                  ? 'text-emerald-400'
                  : isCurrent
                  ? 'text-blue-300 font-semibold'
                  : 'text-text-3 opacity-40'
              }`}
            >
              <span className="w-3 text-center">{isDone ? '✓' : isCurrent ? '●' : '○'}</span>
              <span className="text-[11px]">{step}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
