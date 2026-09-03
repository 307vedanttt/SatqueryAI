import React, { useRef } from 'react';
import type { InputConfiguration } from '../../types';

interface QuerySectionProps {
  query: string;
  onQueryChange: (q: string) => void;
  onSubmit: () => void;
  onClear?: () => void;
  isAnalyzing: boolean;
  canAnalyze: boolean;
  hasResult?: boolean;
  configuration?: InputConfiguration;
}

export const QuerySection: React.FC<QuerySectionProps> = ({
  query,
  onQueryChange,
  onSubmit,
  onClear,
  isAnalyzing,
  canAnalyze,
  hasResult = false,
  configuration = 'SINGLE_OPTICAL',
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const maxLength = 500;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.key === 'Enter' && !e.shiftKey) || (e.key === 'Enter' && e.ctrlKey)) {
      e.preventDefault();
      if (canAnalyze && !isAnalyzing) {
        onSubmit();
      }
    }
  };

  // Preset suggestions based on configuration
  const defaultSuggestions = [
    'What is visible in this image?',
    'Where are the major buildings?',
    'Identify water bodies.',
    'Describe the land cover.',
    'What changed between these images?',
  ];

  // Specific suggestion chips
  const suggestions =
    configuration === 'OPTICAL_SAR_PAIR'
      ? [
          'What complementary information do these sensors provide?',
          'Where are the major buildings and water bodies?',
          'What does the optical image show vs what SAR reveals?',
        ]
      : configuration === 'BI_TEMPORAL'
      ? [
          'What changed between these images?',
          'Where are the major buildings that changed?',
          'Describe the land cover differences.',
        ]
      : defaultSuggestions;

  return (
    <div className="query-section card p-4 bg-[#0a101d] rounded-xl border border-slate-800 shadow-sm flex flex-col gap-3">
      {/* Header & Subtitle */}
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
            <span className="text-cyan-400">💬</span>
            <span>Ask Question</span>
          </h3>
          <p className="text-[11px] text-slate-400 font-sans mt-0.5">
            Ask a natural-language question about the imagery.
          </p>
        </div>
        <span className="text-[10px] font-mono text-slate-500 hidden sm:inline">
          Press ↵ Enter
        </span>
      </div>

      {/* Query Input Box */}
      <div className="relative flex flex-col gap-2">
        <textarea
          id="query-input"
          ref={textareaRef}
          value={query}
          maxLength={maxLength}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="What is visible in this image?"
          rows={3}
          disabled={isAnalyzing}
          className="w-full bg-[#070d18] text-slate-100 text-xs p-3 rounded-lg border border-slate-800 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/40 resize-none transition-all placeholder:text-slate-500 leading-relaxed font-sans"
        />

        {/* Bottom Status, Character Count & Actions */}
        <div className="flex flex-wrap justify-between items-center gap-2">
          <div className="flex items-center gap-2">
            <span className="text-[10.5px] font-mono text-slate-500">
              {query.length} / {maxLength}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {query && (
              <button
                type="button"
                onClick={onClear}
                disabled={isAnalyzing}
                className="px-2.5 py-1.5 rounded-lg font-mono text-xs text-slate-400 hover:text-slate-100 bg-slate-900 hover:bg-slate-800 border border-slate-800 transition-colors cursor-pointer"
                title="Clear query"
              >
                Clear
              </button>
            )}

            {/* Primary Analyze CTA */}
            <button
              type="button"
              onClick={onSubmit}
              disabled={!canAnalyze || isAnalyzing}
              className={`px-4 py-2 rounded-lg font-mono font-bold text-xs tracking-wide flex items-center gap-2 transition-all ${
                canAnalyze && !isAnalyzing
                  ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-md shadow-blue-600/30 cursor-pointer active:scale-[0.98]'
                  : 'bg-slate-800/80 text-slate-500 cursor-not-allowed border border-slate-700/50'
              }`}
            >
              {isAnalyzing ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : hasResult ? (
                <>
                  <span>✦</span>
                  <span>Analysis Complete</span>
                </>
              ) : (
                <>
                  <span>✦</span>
                  <span>
                    {!canAnalyze
                      ? !query.trim()
                        ? 'Enter question to continue'
                        : 'Upload imagery to continue'
                      : 'Analyze Imagery'}
                  </span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Suggested Question Chips */}
      <div className="pt-2 border-t border-slate-800/80 flex flex-col gap-1.5">
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
          Suggested Questions:
        </span>
        <div className="flex flex-wrap gap-1.5">
          {suggestions.map((q, idx) => (
            <button
              key={idx}
              type="button"
              disabled={isAnalyzing}
              onClick={() => {
                onQueryChange(q);
                textareaRef.current?.focus();
              }}
              className="text-[11px] text-left px-2.5 py-1 rounded-md bg-[#0e1628] hover:bg-slate-800 border border-slate-800/90 text-slate-300 hover:text-white transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            >
              "{q}"
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
