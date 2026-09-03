import React, { useRef } from 'react';
import type { InputConfiguration } from '../../types';
import { SuggestedQuestions } from './SuggestedQuestions';

interface QuerySectionProps {
  query: string;
  onQueryChange: (q: string) => void;
  onSubmit: () => void;
  onClear?: () => void;
  isAnalyzing: boolean;
  canAnalyze: boolean;
  configuration?: InputConfiguration;
}

export const QuerySection: React.FC<QuerySectionProps> = ({
  query,
  onQueryChange,
  onSubmit,
  onClear,
  isAnalyzing,
  canAnalyze,
  configuration,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.key === 'Enter' && !e.shiftKey) || (e.key === 'Enter' && e.ctrlKey)) {
      e.preventDefault();
      if (canAnalyze && !isAnalyzing) {
        onSubmit();
      }
    }
  };

  return (
    <div className="query-section card p-4 bg-[#0d1424] rounded-xl border border-slate-800 shadow-sm flex flex-col gap-3">
      <div className="flex justify-between items-center">
        <label htmlFor="query-input" className="text-xs font-bold text-slate-200 flex items-center gap-2 tracking-wide uppercase font-mono">
          <span className="text-cyan-400">⚡</span>
          <span>Natural Language Query</span>
        </label>
        <span className="text-[10px] font-mono text-slate-500">Press ↵ Enter to run</span>
      </div>

      <div className="relative flex flex-col gap-2.5">
        <textarea
          id="query-input"
          ref={textareaRef}
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about the imagery (e.g., 'What changed between these dates?' or 'Where are the buildings?')..."
          rows={3}
          disabled={isAnalyzing}
          className="w-full bg-[#080d18] text-slate-100 text-xs p-3 rounded-lg border border-slate-800 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/40 resize-none transition-all placeholder:text-slate-500 leading-relaxed font-sans"
        />

        <div className="flex justify-between items-center">
          <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5">
            {canAnalyze ? (
              <span className="text-emerald-400 font-semibold">● Ready for analysis</span>
            ) : (
              <span className="text-slate-500">Upload imagery to enable query</span>
            )}
          </span>

          <div className="flex items-center gap-2">
            {query && (
              <button
                type="button"
                onClick={onClear}
                disabled={isAnalyzing}
                className="px-3 py-1.5 rounded-lg font-mono text-xs text-slate-400 hover:text-slate-100 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 transition-colors cursor-pointer"
                title="Clear query"
              >
                Clear
              </button>
            )}

            <button
              type="button"
              onClick={onSubmit}
              disabled={!canAnalyze || isAnalyzing}
              className={`px-4 py-1.5 rounded-lg font-mono font-bold text-xs uppercase tracking-wide flex items-center gap-2 transition-all ${
                canAnalyze && !isAnalyzing
                  ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/30 cursor-pointer'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/40'
              }`}
            >
              {isAnalyzing ? (
                <>
                  <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <span>🚀</span>
                  <span>Analyze</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Suggested Questions */}
      <div className="pt-2 border-t border-slate-800/80">
        <SuggestedQuestions
          configuration={configuration}
          onSelectQuestion={(q) => {
            onQueryChange(q);
            textareaRef.current?.focus();
          }}
          disabled={isAnalyzing}
        />
      </div>
    </div>
  );
};
