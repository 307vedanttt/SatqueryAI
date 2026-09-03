import React from 'react';

export const About: React.FC = () => {
  return (
    <div className="about-page flex flex-col gap-6 max-w-4xl mx-auto py-2">
      {/* Header */}
      <div className="p-5 rounded-xl bg-surface border border-glass-border">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🛰️</span>
          <div>
            <h1 className="text-xl font-bold text-text">About SatQuery AI</h1>
            <div className="text-xs font-mono text-accent">
              Multimodal Remote Sensing Intelligence • SIH26167
            </div>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-text-2 leading-relaxed mt-2">
          SatQuery AI is an interactive vision-language workstation designed for multimodal remote-sensing image analysis through natural language text queries. Built for the Smart India Hackathon 2026 (Problem Statement SIH26167) for the ISRO Department of Space.
        </p>
      </div>

      {/* How It Works Diagram */}
      <div className="card p-5 bg-surface rounded-xl border border-glass-border space-y-3">
        <h2 className="text-sm font-bold text-text flex items-center gap-2">
          <span>⚙️</span>
          <span>HOW IT WORKS — BOUNDED ORCHESTRATION PIPELINE</span>
        </h2>

        <div className="p-4 rounded-xl bg-surface-2 border border-glass-border font-mono text-xs text-center text-text-2 overflow-x-auto leading-loose">
          <div className="text-blue-400 font-bold">USER INPUT (Imagery + Text Query)</div>
          <div className="text-text-3">↓</div>
          <div className="text-emerald-400 font-semibold">1. INGESTION & GEOSPATIAL VALIDATION (CRS, Resolution, Overlap)</div>
          <div className="text-text-3">↓</div>
          <div className="text-purple-400 font-semibold">2. CONFIGURATION DETECTION (Single, Bi-Temporal, Optical + SAR)</div>
          <div className="text-text-3">↓</div>
          <div className="text-cyan-400 font-bold">3. BOUNDED PYTHON ROUTER (Deterministic Intent Classification)</div>
          <div className="text-text-3">↓</div>
          <div className="flex justify-center gap-4 text-[11px] text-text">
            <span className="px-2 py-1 rounded bg-surface border border-glass-border">VQA / Captioning</span>
            <span className="px-2 py-1 rounded bg-surface border border-glass-border">Spatial Grounding</span>
            <span className="px-2 py-1 rounded bg-surface border border-glass-border">Change Detection</span>
            <span className="px-2 py-1 rounded bg-surface border border-glass-border">Optical-SAR Fusion</span>
          </div>
          <div className="text-text-3">↓</div>
          <div className="text-amber-400 font-semibold">4. EVIDENCE SYNTHESIS & CROSS-SENSOR DISAGREEMENT CHECK</div>
          <div className="text-text-3">↓</div>
          <div className="text-emerald-400 font-bold">5. GROUNDED ANSWER + EXPLAINABLE EXECUTION TRACE</div>
        </div>
      </div>

      {/* Why It Is Different */}
      <div className="card p-5 bg-surface rounded-xl border border-glass-border space-y-2.5">
        <h2 className="text-sm font-bold text-text flex items-center gap-2">
          <span>💡</span>
          <span>WHY IT IS DIFFERENT</span>
        </h2>

        <blockquote className="p-3.5 rounded-lg bg-blue-950/30 border-l-4 border-blue-500 text-xs sm:text-sm text-blue-200 italic leading-relaxed">
          "SatQuery AI does not treat every remote-sensing question as the same task. It uses a bounded orchestration layer to select appropriate specialist analysis based on the query and image configuration."
        </blockquote>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 text-xs text-text-2">
          <div className="p-3 rounded-lg bg-surface-2 border border-glass-border/40 space-y-1">
            <div className="font-bold text-text">🚫 Open-Ended Autonomous Frameworks</div>
            <p className="text-[11px] text-text-3 leading-relaxed">
              Autonomous agents can hallucinate steps, enter infinite polling loops, or invent geospatial coordinates not grounded in physical raster bands.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-surface-2 border border-glass-border/40 space-y-1">
            <div className="font-bold text-emerald-400">✓ SatQuery Bounded Planner</div>
            <p className="text-[11px] text-text-3 leading-relaxed">
              Deterministic finite execution graphs with strict pre-conditions (e.g. change detection requires 2 co-registered images with matching CRS).
            </p>
          </div>
        </div>
      </div>

      {/* Supported Analysis Modes */}
      <div className="card p-5 bg-surface rounded-xl border border-glass-border space-y-3">
        <h2 className="text-sm font-bold text-text flex items-center gap-2">
          <span>🛰️</span>
          <span>SUPPORTED ANALYSIS CAPABILITIES</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-surface-2 border border-glass-border/40">
            <span className="font-mono text-cyan-400 font-bold text-[11px] block">1. SINGLE-IMAGE VQA</span>
            <span className="text-text-2 text-[11px] mt-1 block">
              Natural language answers regarding land use, surface coverage, and identifiable geographical landmarks.
            </span>
          </div>

          <div className="p-3 rounded-lg bg-surface-2 border border-glass-border/40">
            <span className="font-mono text-cyan-400 font-bold text-[11px] block">2. SPATIAL GROUNDING</span>
            <span className="text-text-2 text-[11px] mt-1 block">
              Text-prompted spatial localization returning verified bounding boxes [x1, y1, x2, y2] in image pixel coordinates.
            </span>
          </div>

          <div className="p-3 rounded-lg bg-surface-2 border border-glass-border/40">
            <span className="font-mono text-cyan-400 font-bold text-[11px] block">3. OPTICAL + SAR FUSION</span>
            <span className="text-text-2 text-[11px] mt-1 block">
              Cross-sensor joint analysis combining optical reflectance with SAR microwave backscatter dielectric properties.
            </span>
          </div>

          <div className="p-3 rounded-lg bg-surface-2 border border-glass-border/40">
            <span className="font-mono text-cyan-400 font-bold text-[11px] block">4. BI-TEMPORAL CHANGE DETECTION</span>
            <span className="text-text-2 text-[11px] mt-1 block">
              Spatial differencing across two co-registered acquisition dates to detect built-up expansion, deforestation, and water level changes.
            </span>
          </div>
        </div>
      </div>

      {/* Explainability & Safety */}
      <div className="card p-4 rounded-xl bg-surface border border-glass-border flex items-center justify-between gap-4 text-xs font-mono text-text-3">
        <span>Bounded Execution • Zero Silent Failures • Refusal on Low Confidence</span>
        <span className="text-accent font-bold">ISRO SIH26167</span>
      </div>
    </div>
  );
};
