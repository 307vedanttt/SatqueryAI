import React from 'react';
import type { OverlayOptions } from '../../types';

interface ImageLegendProps {
  hasBbox: boolean;
  hasChange: boolean;
  hasSensorComparison: boolean;
  overlays: OverlayOptions;
}

export const ImageLegend: React.FC<ImageLegendProps> = ({
  hasBbox,
  hasChange,
  hasSensorComparison,
  overlays,
}) => {
  if (!overlays.evidence && !overlays.boundingBoxes && !overlays.changeHeatmap) {
    return null;
  }

  return (
    <div className="image-legend flex flex-wrap items-center gap-3 px-3 py-1.5 rounded-lg bg-surface/90 border border-glass-border text-[11px] font-mono">
      <span className="text-text-3 uppercase tracking-wider text-[10px]">LEGEND:</span>

      {hasBbox && overlays.boundingBoxes && (
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm border-2 border-cyan-400 bg-cyan-400/20" />
          <span className="text-text-2">Grounded Object [bbox]</span>
        </div>
      )}

      {hasChange && overlays.changeHeatmap && (
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm border-2 border-amber-400 bg-amber-400/30" />
          <span className="text-text-2">Detected Change Region</span>
        </div>
      )}

      {hasSensorComparison && overlays.evidence && (
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm border-2 border-purple-400 bg-purple-400/20" />
          <span className="text-text-2">Cross-Sensor Observation</span>
        </div>
      )}
    </div>
  );
};
