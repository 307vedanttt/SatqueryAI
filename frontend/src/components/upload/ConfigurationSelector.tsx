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
    subtitle: string;
    description: string;
    badge: string;
    accentColor: string;
    badgeColor: string;
    icon: React.ReactNode;
    tags: string[];
  }> = [
    {
      id: 'single',
      title: 'Single Scene',
      subtitle: 'Optical or SAR Analysis',
      description: 'VQA, captioning, and classification on a single raster.',
      badge: '1 SENSOR',
      accentColor: 'cyan',
      badgeColor: 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60',
      icon: (
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
      ),
      tags: ['VQA', 'Caption', 'Classify'],
    },
    {
      id: 'optical-sar',
      title: 'Optical + SAR',
      subtitle: 'Cross-Modal Fusion Analysis',
      description: 'Fuse optical and SAR radar data for multi-sensor inference.',
      badge: 'CROSS-MODAL',
      accentColor: 'violet',
      badgeColor: 'bg-violet-950/80 text-violet-300 border-violet-700/60',
      icon: (
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="12 2 2 7 12 12 22 7 12 2" />
          <polyline points="2 17 12 22 22 17" />
          <polyline points="2 12 12 17 22 12" />
        </svg>
      ),
      tags: ['SAR Fusion', 'Multi-sensor', 'Radar'],
    },
    {
      id: 'bi-temporal',
      title: 'Bi-Temporal Change',
      subtitle: 'Compare Two Time Points',
      description: 'Detect and localize changes between T1 baseline and T2 target.',
      badge: 'T1 → T2',
      accentColor: 'amber',
      badgeColor: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
      icon: (
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
      ),
      tags: ['Change Detection', 'Temporal', 'T1/T2'],
    },
  ];

  // Accent style maps
  const accentBorder: Record<string, string> = {
    cyan:   'border-cyan-500/70',
    violet: 'border-violet-500/70',
    amber:  'border-amber-500/70',
  };
  const accentGlow: Record<string, string> = {
    cyan:   'shadow-cyan-950/50',
    violet: 'shadow-violet-950/50',
    amber:  'shadow-amber-950/50',
  };
  const accentIcon: Record<string, string> = {
    cyan:   'bg-cyan-950/70 border-cyan-500/40 text-cyan-300',
    violet: 'bg-violet-950/70 border-violet-500/40 text-violet-300',
    amber:  'bg-amber-950/70 border-amber-500/40 text-amber-300',
  };
  const accentDot: Record<string, string> = {
    cyan:   'bg-cyan-400 border-cyan-400',
    violet: 'bg-violet-400 border-violet-400',
    amber:  'bg-amber-400 border-amber-400',
  };
  const accentTag: Record<string, string> = {
    cyan:   'bg-cyan-950/60 text-cyan-400 border-cyan-800/50',
    violet: 'bg-violet-950/60 text-violet-400 border-violet-800/50',
    amber:  'bg-amber-950/60 text-amber-400 border-amber-800/50',
  };
  const accentTitle: Record<string, string> = {
    cyan:   'text-cyan-100',
    violet: 'text-violet-100',
    amber:  'text-amber-100',
  };

  return (
    <div className="configuration-selector flex flex-col gap-2.5">
      {/* Section Header */}
      <div className="flex justify-between items-center px-0.5">
        <span className="font-mono text-[11px] font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <span className="text-cyan-400">◈</span>
          <span>ANALYSIS CONFIGURATION</span>
        </span>
        <span className="text-[10px] font-mono text-slate-500 uppercase">
          {configs.length} MODES
        </span>
      </div>

      {/* 3 Bento Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {configs.map((cfg) => {
          const isSelected = selectedMode === cfg.id;
          const color = cfg.accentColor;

          return (
            <button
              key={cfg.id}
              type="button"
              disabled={disabled}
              onClick={() => !disabled && onSelectMode(cfg.id)}
              className={[
                'relative flex flex-col justify-between p-4 rounded-xl border text-left transition-all duration-200',
                'select-none cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60',
                isSelected
                  ? `bg-slate-900/95 backdrop-blur-xl ${accentBorder[color]} shadow-xl ${accentGlow[color]}`
                  : 'bg-slate-950/50 backdrop-blur-md border-white/8 hover:border-white/20 hover:bg-slate-900/50',
                disabled ? 'opacity-50 cursor-not-allowed' : '',
              ].join(' ')}
            >
              {/* Selection Indicator — top right corner */}
              <div
                className={`absolute top-3 right-3 w-4 h-4 rounded-full border-2 flex items-center justify-center transition-all duration-150 ${
                  isSelected
                    ? `${accentDot[color]} shadow-sm`
                    : 'border-slate-700 bg-slate-900/60'
                }`}
              >
                {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
              </div>

              {/* Top Section: Icon + Badge */}
              <div className="flex flex-col gap-3 mb-3">
                <div className="flex items-center justify-between">
                  <div
                    className={`p-2 rounded-lg border transition-colors ${
                      isSelected ? accentIcon[color] : 'bg-slate-900/60 border-white/8 text-slate-500'
                    }`}
                  >
                    {cfg.icon}
                  </div>
                  <span
                    className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase tracking-wide ${
                      isSelected ? cfg.badgeColor : 'bg-slate-900 border-white/8 text-slate-500'
                    }`}
                  >
                    {cfg.badge}
                  </span>
                </div>

                {/* Title & Subtitle */}
                <div>
                  <h4 className={`text-sm font-bold tracking-tight leading-tight transition-colors ${
                    isSelected ? accentTitle[color] : 'text-slate-400'
                  }`}>
                    {cfg.title}
                  </h4>
                  <p className={`text-[10px] font-mono font-semibold uppercase tracking-wide mt-0.5 transition-colors ${
                    isSelected ? 'text-slate-400' : 'text-slate-600'
                  }`}>
                    {cfg.subtitle}
                  </p>
                </div>
              </div>

              {/* Description */}
              <p className={`text-[11px] font-sans leading-snug transition-colors mb-3 ${
                isSelected ? 'text-slate-300' : 'text-slate-500'
              }`}>
                {cfg.description}
              </p>

              {/* Tags */}
              <div className="flex flex-wrap gap-1">
                {cfg.tags.map((tag) => (
                  <span
                    key={tag}
                    className={`text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded border uppercase transition-colors ${
                      isSelected ? accentTag[color] : 'bg-slate-900/60 border-white/5 text-slate-600'
                    }`}
                  >
                    {tag}
                  </span>
                ))}
              </div>

              {/* Bottom Selected State Glow Bar */}
              {isSelected && (
                <div
                  className={`absolute bottom-0 left-3 right-3 h-[2px] rounded-full ${
                    color === 'cyan' ? 'bg-gradient-to-r from-transparent via-cyan-400/60 to-transparent' :
                    color === 'violet' ? 'bg-gradient-to-r from-transparent via-violet-400/60 to-transparent' :
                    'bg-gradient-to-r from-transparent via-amber-400/60 to-transparent'
                  }`}
                />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
