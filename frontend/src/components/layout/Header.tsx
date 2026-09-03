import React from 'react';
import type { HealthResponse, NavigationTab } from '../../types';

interface HeaderProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  health: HealthResponse | null;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onSelectTab, health }) => {
  const navItems: Array<{ id: NavigationTab; label: string; icon: string }> = [
    { id: 'workspace', label: 'Analysis', icon: '🛰️' },
    { id: 'history', label: 'Audit History', icon: '📜' },
    { id: 'reports', label: 'Reports', icon: '📊' },
    { id: 'evaluation', label: 'Model Scorecard', icon: '🎯' },
    { id: 'about', label: 'Architecture', icon: 'ℹ️' },
  ];

  return (
    <header className="header flex items-center justify-between py-3.5 border-b border-slate-800/80 mb-5" role="banner">
      {/* Brand & Logo */}
      <div
        className="header-brand flex items-center gap-3 cursor-pointer select-none group"
        onClick={() => onSelectTab('workspace')}
      >
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-700 to-cyan-500 flex items-center justify-center text-lg shadow-md shadow-cyan-500/20 border border-white/15 group-hover:scale-105 transition-transform">
          🛰️
        </div>
        <div>
          <div className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-cyan-300 bg-clip-text text-transparent">
            SATQUERY AI
          </div>
          <div className="text-[11px] font-medium text-slate-400 tracking-wide">
            Multimodal Remote Sensing Intelligence
          </div>
        </div>
      </div>

      {/* Center Segmented Navigation */}
      <nav className="header-nav hidden md:flex items-center gap-1 bg-slate-900/80 backdrop-blur-md p-1 rounded-full border border-slate-800/80 shadow-inner" aria-label="Main Navigation">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                isActive
                  ? 'bg-blue-600 text-white font-semibold shadow-sm shadow-blue-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
              onClick={() => onSelectTab(item.id)}
              aria-current={isActive ? 'page' : undefined}
            >
              <span className="text-xs">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Status & Problem Statement Badge */}
      <div className="header-badge flex items-center gap-2.5">
        <span
          className="px-2.5 py-1 rounded-full font-mono text-[11px] font-semibold bg-blue-950/60 text-cyan-300 border border-blue-800/60"
          title="Smart India Hackathon 2026 - ISRO Problem Statement"
        >
          SIH26167
        </span>

        {health?.demo_mode && (
          <span
            className="px-2 py-0.5 rounded-full font-mono text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700 hidden sm:inline"
            title="Running bounded offline demonstration specialists"
          >
            DEMO MODE
          </span>
        )}

        <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 pl-1" title="Backend Connection State">
          <span className={`status-dot ${health ? 'ok' : 'degraded'}`} />
          <span className="text-[11px] font-semibold text-slate-300">
            {health ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>
      </div>
    </header>
  );
};
