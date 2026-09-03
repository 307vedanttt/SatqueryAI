import React, { useRef } from 'react';
import type { InputConfiguration } from '../../types';
import { SuggestedQuestions } from './SuggestedQuestions';

interface QuerySectionProps {
  query: string;
  onQueryChange: (q: string) => void;
  onSubmit: () => void;
  isAnalyzing: boolean;
  canAnalyze: boolean;
  configuration?: InputConfiguration;
}

export const QuerySection: React.FC<QuerySectionProps> = ({
  query,
  onQueryChange,
  onSubmit,
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
    <div className="query-section card p-4 bg-surface rounded-xl border border-glass-border shadow-lg">
      <div className="flex justify-between items-center mb-2">
        <label htmlFor="query-input" className="text-xs font-semibold text-text flex items-center gap-1.5">
          <span>🔍</span>
          <span>NATURAL LANGUAGE QUERY</span>
        </label>
        <span className="text-[10px] font-mono text-text-3">Press Enter to run</span>
      </div>

      <div className="relative">
        <textarea
          id="query-input"
          ref={textareaRef}
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about the imagery (e.g., 'What changed between these images?' or 'Where are the buildings?')..."
          rows={3}
          disabled={isAnalyzing}
          className="w-full bg-surface-2 text-text text-xs p-3 rounded-lg border border-glass-border focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500/50 resize-none transition-all placeholder:text-text-3"
        />

        <div className="flex justify-between items-center mt-2">
          <span className="text-[11px] text-text-3 font-mono">
            {canAnalyze ? '✓ Ready for analysis' : 'Upload imagery to start'}
          </span>

          <button
            type="button"
            onClick={onSubmit}
            disabled={!canAnalyze || isAnalyzing}
            className={`px-4 py-2 rounded-lg font-mono font-bold text-xs uppercase tracking-wide flex items-center gap-2 transition-all ${
              canAnalyze && !isAnalyzing
                ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20 cursor-pointer'
                : 'bg-surface-2 text-text-3 cursor-not-allowed border border-glass-border/40'
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

      {/* Suggested Questions based on configuration */}
      <SuggestedQuestions
        configuration={configuration}
        onSelectQuestion={(q) => {
          onQueryChange(q);
          textareaRef.current?.focus();
        }}
        disabled={isAnalyzing}
      />
    </div>
  );
};
