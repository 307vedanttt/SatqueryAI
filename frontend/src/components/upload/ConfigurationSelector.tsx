import React from 'react';
import type { AnalysisMode } from './ModeAwareUploader';

interface ConfigurationSelectorProps {
  selectedMode: AnalysisMode;
  onSelectMode: (mode: AnalysisMode) => void;
  disabled?: boolean;
}

export const ConfigurationSelector: React.FC<ConfigurationSelectorProps> = ({
  selectedMode,
  onSelectMode,
  disabled = false,
}) => {
  const configs: Array<{
    id: AnalysisMode;
    title: string;
    description: string;
    icon: string;
    badge: string;
  }> = [
    {
      id: 'single',
      title: 'Single Scene',
      description: 'Single optical or SAR analysis',
      icon: '◈',
      badge: '1 SENSOR',
    },
    {
      id: 'optical-sar',
      title: 'Optical + SAR',
      description: 'Cross-modal optical + radar analysis',
      icon: '◫',
      badge: 'CROSS-MODAL',
    },
    {
      id: 'bi-temporal',
      title: 'Bi-Temporal Change',
      description: 'Compare imagery across two time points',
      icon: '⏱',
      badge: 'T1 → T2',
    },
  ];

  return (
    <div className="configuration-selector flex flex-col gap-2">
      <div className="flex justify-between items-center px-1">
        <label className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
          <span className="text-cyan-400">⚙</span>
          <span>CONFIGURATION SELECTOR</span>
        </label>
        <span className="text-[10px] font-mono text-slate-500">
          SELECT ANALYSIS ARCHITECTURE
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {configs.map((cfg) => {
          const isSelected = selectedMode === cfg.id;

          return (
            <div
              key={cfg.id}
              onClick={() => !disabled && onSelectMode(cfg.id)}
              className={`relative flex flex-col justify-between p-4 rounded-xl border transition-all cursor-pointer select-none ${
                isSelected
                  ? 'bg-[#0b162b] border-cyan-400 shadow-[0_0_24px_rgba(6,182,212,0.35)] ring-1 ring-cyan-400/80 -translate-y-0.5'
                  : 'bg-[#070d18] border-slate-800 hover:border-slate-700 hover:bg-[#0a1222] hover:-translate-y-0.5'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {/* Top Row: Icon + Badge + Radio Indicator */}
              <div className="flex justify-between items-start mb-2.5">
                <div className="flex items-center gap-2">
                  <span className={`text-lg font-bold ${isSelected ? 'text-cyan-400' : 'text-slate-400'}`}>
                    {cfg.icon}
                  </span>
                  <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-[#040812] border border-slate-800 text-cyan-400 uppercase">
                    {cfg.badge}
                  </span>
                </div>

                {/* Radio Dot Indicator */}
                <div
                  className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${
                    isSelected
                      ? 'border-cyan-400 bg-cyan-400 shadow-[0_0_10px_#22d3ee]'
                      : 'border-slate-700 bg-slate-900'
                  }`}
                >
                  {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-slate-950" />}
                </div>
              </div>

              {/* Title & Description */}
              <div>
                <h4
                  className={`text-xs font-bold tracking-tight mb-1 transition-colors ${
                    isSelected ? 'text-white' : 'text-slate-300'
                  }`}
                >
                  {cfg.title}
                </h4>
                <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
                  {cfg.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
