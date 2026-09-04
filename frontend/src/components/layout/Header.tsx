import React, { useState, useRef, useEffect } from 'react';
import type { HealthResponse, NavigationTab } from '../../types';

interface HeaderProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  health: HealthResponse | null;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onSelectTab, health }) => {
  const [showSettings, setShowSettings] = useState(false);
  const settingsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setShowSettings(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navItems: Array<{ id: NavigationTab; label: string; icon: React.ReactNode }> = [
    {
      id: 'home',
      label: 'Home',
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
      ),
    },
    {
      id: 'workspace',
      label: 'Analysis',
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" />
          <circle cx="12" cy="12" r="4" />
          <line x1="12" y1="3" x2="12" y2="21" />
          <line x1="3" y1="12" x2="21" y2="12" />
        </svg>
      ),
    },
    {
      id: 'history',
      label: 'Audit History',
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 8v4l3 3" />
          <path d="M3.05 11a9 9 0 1 1 .5 4m-.5-4v-4m0 4h4" />
        </svg>
      ),
    },
    {
      id: 'reports',
      label: 'Reports',
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 20V10M12 20V4M6 20v-6" />
        </svg>
      ),
    },
    {
      id: 'evaluation',
      label: 'Model Scorecard',
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
          <path d="M12 3v3m0 12v3m9-9h-3M6 12H3" />
        </svg>
      ),
    },
    {
      id: 'about',
      label: 'Architecture',
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="12 2 2 7 12 12 22 7 12 2" />
          <polyline points="2 17 12 22 22 17" />
          <polyline points="2 12 12 17 22 12" />
        </svg>
      ),
    },
  ];


  return (
    <header className="sticky top-6 z-50 w-full max-w-[1400px] mx-auto px-6" role="banner">
      {/* Glassmorphic Container with subtle neumorphic shadow */}
      <div className="flex flex-wrap lg:flex-nowrap items-center justify-between px-8 py-5 rounded-3xl border border-white/10 bg-slate-900/40 backdrop-blur-2xl shadow-[10px_10px_20px_rgba(0,0,0,0.5),-10px_-10px_20px_rgba(255,255,255,0.03)]">
        {/* Left: SATQUERY AI Branding & Satellite Logo */}
        <div
          className="flex items-center gap-3 cursor-pointer select-none group"
          onClick={() => onSelectTab('workspace')}
        >
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-2xl tracking-tight text-white group-hover:text-slate-200 transition-colors drop-shadow-md">
                SATQUERY <span className="text-cyan-400">AI</span>
              </span>
            </div>
            <span className="text-[11px] font-medium text-slate-400 tracking-wider font-sans uppercase">
              Multimodal Remote Sensing Intelligence
            </span>
          </div>
        </div>

        {/* Center: Navigation Bar */}
        <nav className="hidden lg:flex items-center gap-4" aria-label="Main Navigation">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`relative px-5 py-2.5 rounded-xl text-sm font-bold transition-all duration-300 cursor-pointer select-none flex items-center justify-center
                  ${
                    isActive 
                      ? 'text-cyan-400 bg-slate-900/50 shadow-[inset_4px_4px_8px_rgba(0,0,0,0.6),inset_-4px_-4px_8px_rgba(255,255,255,0.05)] border border-black/20' 
                      : 'text-slate-300 bg-slate-800/40 hover:bg-slate-800/60 hover:text-white shadow-[4px_4px_8px_rgba(0,0,0,0.4),-4px_-4px_8px_rgba(255,255,255,0.05)] border border-white/5 hover:translate-y-[-1px]'
                  }
                `}
                onClick={() => onSelectTab(item.id)}
                aria-current={isActive ? 'page' : undefined}
              >
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right: Badges, Status & Settings */}
        <div className="flex items-center gap-6">
          <div
            className="flex items-center gap-3 px-4 py-2 rounded-xl bg-slate-900/50 shadow-[inset_2px_2px_5px_rgba(0,0,0,0.5),inset_-2px_-2px_5px_rgba(255,255,255,0.02)] border border-black/20 font-mono text-xs font-bold text-slate-300"
            title="Backend API Connection State"
          >
            <span className={`w-2.5 h-2.5 rounded-full ${health ? 'bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)] animate-pulse' : 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.8)]'}`} />
            <span className="tracking-wider">{health ? 'SYSTEM ONLINE' : 'OFFLINE'}</span>
          </div>

          {/* Settings Popover */}
          <div className="relative" ref={settingsRef}>
            <button
              type="button"
              onClick={() => setShowSettings(!showSettings)}
              className="p-2.5 rounded-xl text-slate-400 bg-slate-800/40 shadow-[4px_4px_8px_rgba(0,0,0,0.4),-4px_-4px_8px_rgba(255,255,255,0.05)] border border-white/5 hover:bg-slate-800/60 hover:text-white transition-all hover:translate-y-[-1px] cursor-pointer"
            >
              <svg className="w-5 h-5 drop-shadow-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </button>

            {showSettings && (
              <div className="absolute right-0 mt-4 w-72 p-5 bg-slate-900/80 border border-white/10 rounded-2xl shadow-[10px_10px_20px_rgba(0,0,0,0.6),-5px_-5px_15px_rgba(255,255,255,0.05)] backdrop-blur-2xl z-50 text-xs font-sans text-slate-300">
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/10">
                  <span className="font-bold text-white font-mono uppercase tracking-wider text-[11px] drop-shadow">System Telemetry</span>
                  <span className="text-[10px] text-cyan-400 font-mono font-bold drop-shadow">v{health?.version || '1.0.0'}</span>
                </div>
                <div className="space-y-3 font-mono text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-semibold">Environment:</span>
                    <span className="text-slate-200">Production</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-semibold">LLM Provider:</span>
                    <span className="text-slate-200">{health?.llm_provider || 'connected'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-semibold">Vision Node:</span>
                    <span className="text-slate-200">{health?.vision_provider || 'active'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-semibold">Database:</span>
                    <span className="text-emerald-400 font-bold drop-shadow">{health?.database || 'connected'}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Mobile Navigation Row */}
        <div className="lg:hidden w-full flex items-center justify-around pt-4 mt-4 border-t border-white/10">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`flex flex-col items-center gap-1.5 p-3 rounded-xl transition-all duration-300 ${
                  isActive 
                    ? 'text-cyan-400 bg-slate-900/50 shadow-[inset_3px_3px_6px_rgba(0,0,0,0.6),inset_-3px_-3px_6px_rgba(255,255,255,0.05)] border border-black/20' 
                    : 'text-slate-400 bg-slate-800/40 hover:text-white shadow-[3px_3px_6px_rgba(0,0,0,0.4),-3px_-3px_6px_rgba(255,255,255,0.05)] border border-white/5'
                }`}
                onClick={() => onSelectTab(item.id)}
              >
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};

