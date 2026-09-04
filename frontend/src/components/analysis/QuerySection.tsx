import React, { useRef, useState } from 'react';
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
  error?: string | null;
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
  error,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isFocused, setIsFocused] = useState(false);
  const maxLength = 500;
  const charCount = query.length;
  const charPercent = Math.round((charCount / maxLength) * 100);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.key === 'Enter' && !e.shiftKey) || (e.key === 'Enter' && e.ctrlKey)) {
      e.preventDefault();
      if (canAnalyze && !isAnalyzing) {
        onSubmit();
      }
    }
  };

  // Configuration-aware suggested questions
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
      : [
          'What is visible in this image?',
          'Where are the major buildings?',
          'Identify water bodies.',
          'Describe the land cover.',
          'What changed between these images?',
        ];

  // Derive button state
  const isDisabled = !canAnalyze || isAnalyzing;
  const ctaState: 'disabled' | 'loading' | 'success' | 'ready' = isAnalyzing
    ? 'loading'
    : hasResult && canAnalyze
    ? 'success'
    : 'ready';

  const ctaLabel = {
    loading: 'Analyzing...',
    success: 'Re-Analyze Imagery',
    ready: canAnalyze ? 'Analyze Imagery' : !query.trim() ? 'Enter question first' : 'Upload imagery first',
    disabled: !query.trim() ? 'Enter question first' : 'Upload imagery first',
  }[isDisabled ? 'disabled' : ctaState];

  return (
    <div className="query-section flex flex-col gap-0 rounded-xl border border-white/10 bg-slate-950/75 backdrop-blur-xl shadow-xl shadow-black/40 overflow-hidden">

      {/* Panel Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/8 bg-slate-900/60">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-cyan-950/70 border border-cyan-500/30 text-cyan-400">
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <div>
            <h3 className="font-mono text-xs font-bold text-slate-100 uppercase tracking-wider">
              ASK QUESTION
            </h3>
            <p className="text-[10.5px] text-slate-400 font-sans leading-tight mt-0.5">
              Ask a natural-language question about the imagery.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden sm:flex items-center gap-1 text-[10px] font-mono text-slate-500 bg-slate-900/80 border border-white/8 px-2 py-0.5 rounded">
            <kbd className="font-mono">↵</kbd>
            <span>to submit</span>
          </span>
          <span className="hidden sm:flex items-center gap-1 text-[10px] font-mono text-slate-500 bg-slate-900/80 border border-white/8 px-2 py-0.5 rounded">
            <kbd className="font-mono">⇧↵</kbd>
            <span>new line</span>
          </span>
        </div>
      </div>

      {/* Textarea Area */}
      <div className={`relative transition-all duration-150 ${isFocused ? 'bg-slate-900/80' : 'bg-slate-950/60'}`}>
        <textarea
          id="query-input"
          ref={textareaRef}
          value={query}
          maxLength={maxLength}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="e.g. What structures are visible near the water body?"
          rows={4}
          disabled={isAnalyzing}
          className={`w-full bg-transparent text-slate-100 text-[13px] px-4 py-3.5 border-0 focus:outline-none resize-none transition-colors placeholder:text-slate-500 leading-relaxed font-sans ${
            isAnalyzing ? 'cursor-not-allowed opacity-70' : ''
          }`}
        />

        {/* Focus ring — rendered as absolute inset border */}
        {isFocused && (
          <div className="absolute inset-0 pointer-events-none ring-1 ring-inset ring-cyan-500/40" />
        )}

        {/* Character counter — bottom right of textarea */}
        <div className="absolute bottom-2.5 right-3 flex items-center gap-1.5 pointer-events-none">
          {/* Mini progress arc */}
          <svg className="w-4 h-4 -rotate-90" viewBox="0 0 16 16">
            <circle cx="8" cy="8" r="6" stroke="rgba(100,116,139,0.25)" strokeWidth="2" fill="none" />
            <circle
              cx="8" cy="8" r="6"
              stroke={charPercent > 85 ? '#f87171' : charPercent > 60 ? '#fbbf24' : '#22d3ee'}
              strokeWidth="2"
              fill="none"
              strokeDasharray={`${Math.PI * 12}`}
              strokeDashoffset={`${Math.PI * 12 * (1 - charPercent / 100)}`}
              strokeLinecap="round"
            />
          </svg>
          <span className={`text-[10px] font-mono tabular-nums ${
            charPercent > 85 ? 'text-red-400' : charPercent > 60 ? 'text-amber-400' : 'text-slate-500'
          }`}>
            {charCount}/{maxLength}
          </span>
        </div>
      </div>

      {/* Suggested Question Chips */}
      <div className="px-4 pt-2 pb-3 border-t border-white/5 flex flex-col gap-2">
        <div className="flex items-center gap-1.5">
          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">QUICK PROMPTS</span>
          <div className="flex-1 h-[1px] bg-white/5" />
        </div>
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
              className={`group text-[11px] text-left px-2.5 py-1.5 rounded-lg border transition-all duration-150 font-sans leading-snug ${
                query === q
                  ? 'bg-cyan-950/70 border-cyan-500/50 text-cyan-300'
                  : 'bg-slate-900/70 border-white/8 text-slate-400 hover:border-cyan-500/30 hover:bg-slate-800/80 hover:text-slate-200'
              } disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer`}
            >
              <span className="opacity-50 mr-1 group-hover:opacity-80 transition-opacity">↗</span>
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mx-4 mb-3 p-2.5 rounded-lg bg-rose-950/50 border border-rose-500/40 text-[11px] font-mono text-rose-300 flex items-center gap-2">
          <svg className="w-3.5 h-3.5 shrink-0 text-rose-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Action Bar */}
      <div className="flex items-center justify-between gap-3 px-4 py-3 bg-slate-900/60 border-t border-white/8">
        {/* Left: Clear */}
        <div className="flex items-center gap-2">
          {query && !isAnalyzing && (
            <button
              type="button"
              onClick={onClear}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg font-mono text-[11px] text-slate-400 hover:text-white bg-slate-900/80 hover:bg-slate-800 border border-white/8 hover:border-white/20 transition-all cursor-pointer"
            >
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
              Clear
            </button>
          )}

          {/* Status hint when disabled */}
          {!canAnalyze && !isAnalyzing && (
            <span className="text-[10.5px] font-mono text-slate-500 flex items-center gap-1">
              <svg className="w-3 h-3 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              {!query.trim() ? 'Enter a question above' : 'Upload satellite imagery first'}
            </span>
          )}
        </div>

        {/* Right: Primary CTA */}
        <button
          type="button"
          onClick={onSubmit}
          disabled={isDisabled}
          className={[
            'relative flex items-center gap-2.5 px-5 py-2.5 rounded-xl font-mono font-bold text-[12px] tracking-wider uppercase transition-all duration-200 select-none',
            ctaState === 'loading'
              ? 'bg-slate-800 border border-cyan-500/30 text-cyan-300 cursor-not-allowed'
              : ctaState === 'success'
              ? 'bg-emerald-600 hover:bg-emerald-500 border border-emerald-400/60 text-white shadow-lg shadow-emerald-900/50 cursor-pointer active:scale-95'
              : isDisabled
              ? 'bg-slate-800/60 border border-white/8 text-slate-500 cursor-not-allowed opacity-60'
              : 'bg-cyan-500 hover:bg-cyan-400 border border-cyan-400/80 text-slate-950 shadow-lg shadow-cyan-950/60 hover:shadow-cyan-900/70 cursor-pointer active:scale-[0.97] hover:scale-[1.02]',
          ].join(' ')}
        >
          {ctaState === 'loading' ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-cyan-400/40 border-t-cyan-300 rounded-full animate-spin shrink-0" />
              <span>Analyzing...</span>
            </>
          ) : ctaState === 'success' ? (
            <>
              <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>Re-Analyze</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
                <line x1="11" y1="8" x2="11" y2="14" />
                <line x1="8" y1="11" x2="14" y2="11" />
              </svg>
              <span>{ctaLabel}</span>
            </>
          )}

          {/* Subtle shimmer line at bottom of button when active */}
          {!isDisabled && ctaState !== 'loading' && (
            <span className="absolute bottom-0 left-2 right-2 h-[1px] rounded-full bg-white/30 pointer-events-none" />
          )}
        </button>
      </div>
    </div>
  );
};
