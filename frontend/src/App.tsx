import React, { useEffect, useState } from 'react';
import type { HealthResponse, NavigationTab } from './types';
import { getHealth } from './services/api';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { Workspace } from './pages/Workspace';
import { History } from './pages/History';
import { Reports } from './pages/Reports';
import { Evaluation } from './pages/Evaluation';
import { About } from './pages/About';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('workspace');
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err) => console.warn('Health check fallback:', err));
  }, []);

  return (
    <div className="app min-h-screen flex flex-col justify-between">
      {/* Top Application Shell Header */}
      <Header
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        health={health}
      />

      {/* Main Active Page Content */}
      <main className="main-content flex-1 py-4" role="main">
        {activeTab === 'workspace' && <Workspace />}
        {activeTab === 'history' && (
          <History
            onOpenItem={() => {
              setActiveTab('workspace');
            }}
          />
        )}
        {activeTab === 'reports' && <Reports />}
        {activeTab === 'evaluation' && <Evaluation />}
        {activeTab === 'about' && <About />}
      </main>

      {/* Application Footer */}
      <Footer />
    </div>
  );
};
