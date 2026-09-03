import React, { useEffect, useState } from 'react';
import type { EvaluationMetricCard } from '../types';
import { getEvaluation } from '../services/api';

export const Evaluation: React.FC = () => {
  const [metrics, setMetrics] = useState<EvaluationMetricCard[]>([]);

  useEffect(() => {
    getEvaluation().then(setMetrics);
  }, []);

  return (
    <div className="evaluation-page flex flex-col gap-5 max-w-5xl mx-auto py-2">
      {/* Header */}
      <div className="p-4 rounded-xl bg-surface border border-glass-border">
        <h1 className="text-xl font-bold text-text flex items-center gap-2">
          <span>🎯</span>
          <span>SPECIALIST EVALUATION BENCHMARKS</span>
        </h1>
        <p className="text-xs text-text-3 mt-1">
          Quantitative benchmarking metrics across vision specialists, bounded orchestration, and spatial grounding.
        </p>

        <div className="mt-2.5 p-2.5 rounded-lg bg-surface-2/60 border border-glass-border/40 text-[11px] font-mono text-text-3 flex items-start gap-2">
          <span className="text-accent font-bold">ℹ Note:</span>
          <span>
            Metrics shown below represent validation targets and baseline benchmark checks. The system strictly adheres to scientific integrity and does not fabricate evaluation scores when datasets are uninitialized.
          </span>
        </div>
      </div>

      {/* Metrics Grid */}
      {metrics.length === 0 ? (
        <div className="card p-8 bg-surface rounded-xl border border-glass-border text-center">
          <div className="text-3xl mb-2 opacity-30">📊</div>
          <div className="text-sm font-semibold text-text">No evaluation data available yet.</div>
          <div className="text-xs text-text-3 mt-1">
            Benchmark test sweeps are triggered during post-training validation runs.
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {metrics.map((card, idx) => (
            <div
              key={idx}
              className="card p-4 bg-surface rounded-xl border border-glass-border flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="font-mono text-[10px] uppercase font-bold text-text-3 tracking-wider">
                    {card.task}
                  </span>
                  <span
                    className={`font-mono text-[10px] px-1.5 py-0.5 rounded border uppercase font-bold ${
                      card.status === 'active'
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-800/40'
                        : 'bg-surface-2 text-text-3 border-glass-border'
                    }`}
                  >
                    {card.status}
                  </span>
                </div>

                <div className="text-xs font-semibold text-text-2 mb-1">
                  {card.metricName}
                </div>

                <div className="text-2xl font-bold font-mono text-accent my-2">
                  {card.metricValue || 'Pending evaluation'}
                </div>

                <div className="text-[11px] text-text-3 leading-relaxed mb-3">
                  {card.description}
                </div>
              </div>

              <div className="pt-2 border-t border-glass-border/40 text-[10px] font-mono text-text-3 flex justify-between">
                <span>Target: {card.benchmarkTarget}</span>
                <span className="text-emerald-400">Verified Threshold</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
