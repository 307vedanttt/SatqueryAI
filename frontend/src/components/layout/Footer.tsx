import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full max-w-[1400px] mx-auto px-6 py-12 border-t border-white/[0.05] mt-12">
      <div className="flex flex-col lg:flex-row items-center justify-between gap-8 mb-12">
        <div className="text-center lg:text-left">
          <div className="font-extrabold text-sm tracking-tight text-white mb-1">
            SATQUERY <span className="text-cyan-400">AI</span>
          </div>
          <div className="text-[11px] font-sans text-slate-500">
            Multimodal Remote Sensing Intelligence
          </div>
        </div>

        <div className="flex flex-wrap justify-center gap-6 text-[11px] font-mono tracking-widest text-slate-400 uppercase">
          <span className="hover:text-white cursor-pointer transition-colors">Analysis</span>
          <span className="hover:text-white cursor-pointer transition-colors">Architecture</span>
          <span className="hover:text-white cursor-pointer transition-colors">Reports</span>
          <span className="hover:text-white cursor-pointer transition-colors">Audit History</span>
        </div>

        <div className="flex flex-col items-center lg:items-end font-mono text-[11px] tracking-widest text-slate-400">
          <span className="mb-1 text-slate-300 font-bold">SIH26167</span>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-cyan-400">System Online</span>
          </div>
        </div>
      </div>
      
      <div className="flex items-center justify-between pt-6 border-t border-white/[0.02] text-[10px] text-slate-600 font-sans">
        <span>© 2026 SatQuery AI. All rights reserved.</span>
        <span>Multimodal Remote Sensing Intelligence</span>
      </div>
    </footer>
  );
};
