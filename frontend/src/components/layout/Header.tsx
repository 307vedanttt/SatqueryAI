import React from 'react';
import type { HealthResponse, NavigationTab } from '../../types';

interface HeaderProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  health: HealthResponse | null;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onSelectTab, health }) => {
  const navItems: Array<{ id: NavigationTab; label: string; icon: string }> = [
    { id: 'workspace', label: 'Workspace', icon: '🛰️' },
    { id: 'history', label: 'History', icon: '📜' },
    { id: 'reports', label: 'Reports', icon: '📊' },
    { id: 'evaluation', label: 'Evaluation', icon: '🎯' },
    { id: 'about', label: 'About', icon: 'ℹ️' },
  ];

  return (
    <header className="header" role="banner">
      <div className="header-brand" onClick={() => onSelectTab('workspace')} style={{ cursor: 'pointer' }}>
        <div className="header-logo" aria-hidden="true">🛰️</div>
        <div>
          <div className="header-title tracking-tight">SATQUERY AI</div>
          <div className="header-subtitle">Multimodal Remote Sensing Intelligence</div>
        </div>
      </div>

      <nav className="header-nav" aria-label="Main Navigation">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`nav-link ${isActive ? 'active' : ''}`}
              onClick={() => onSelectTab(item.id)}
              aria-current={isActive ? 'page' : undefined}
            >
              <span aria-hidden="true">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="header-badge flex items-center gap-2">
        <span className="badge badge-isro font-mono" title="Smart India Hackathon 2026 - ISRO Department of Space">
          SIH26167
        </span>
        {health?.demo_mode && (
          <span className="badge badge-demo font-mono" title="Running in self-contained demonstration mode">
            DEMO MODE
          </span>
        )}
        <div className="flex items-center gap-1 text-xs font-mono text-text-3 ml-1" title="Backend Connection State">
          <span className={`status-dot ${health ? 'ok' : 'degraded'}`} />
          <span>{health ? 'SYSTEM READY' : 'OFFLINE'}</span>
        </div>
      </div>
    </header>
  );
};
