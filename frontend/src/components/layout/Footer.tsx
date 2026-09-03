import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="footer mt-6 py-4 border-t border-glass-border text-xs text-text-3 flex flex-wrap justify-between items-center gap-2">
      <div className="flex items-center gap-3">
        <span className="font-semibold text-text-2">SATQUERY AI</span>
        <span>•</span>
        <span>SIH 2026 Problem Statement SIH26167</span>
        <span>•</span>
        <span>ISRO Department of Space</span>
      </div>
      <div className="flex items-center gap-4 font-mono text-xs">
        <span>Bounded Python Planner</span>
        <span>•</span>
        <span>Evidence-Grounded AI</span>
        <span>•</span>
        <span>v0.1.0</span>
      </div>
    </footer>
  );
};
