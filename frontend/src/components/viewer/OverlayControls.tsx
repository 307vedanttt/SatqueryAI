import React from 'react';
import type { OverlayOptions } from '../../types';

interface OverlayControlsProps {
  overlays: OverlayOptions;
  onChange: (overlays: OverlayOptions) => void;
  hasBbox: boolean;
  hasChange: boolean;
}

export const OverlayControls: React.FC<OverlayControlsProps> = ({
  overlays,
  onChange,
  hasBbox,
  hasChange,
}) => {
  return (
    <div className="overlay-controls flex items-center gap-3 px-3 py-1.5 rounded-lg bg-surface/90 border border-glass-border text-xs font-mono">
      <span className="text-text-3 uppercase tracking-wider text-[10px]">OVERLAYS:</span>

      <label className="flex items-center gap-1.5 cursor-pointer text-text-2 hover:text-text">
        <input
          type="checkbox"
          checked={overlays.evidence}
          onChange={(e) => onChange({ ...overlays, evidence: e.target.checked })}
          className="rounded text-blue-500"
        />
        <span>Evidence</span>
      </label>

      {hasBbox && (
        <label className="flex items-center gap-1.5 cursor-pointer text-text-2 hover:text-text">
          <input
            type="checkbox"
            checked={overlays.boundingBoxes}
            onChange={(e) => onChange({ ...overlays, boundingBoxes: e.target.checked })}
            className="rounded text-cyan-400"
          />
          <span>Bounding Boxes</span>
        </label>
      )}

      {hasChange && (
        <label className="flex items-center gap-1.5 cursor-pointer text-text-2 hover:text-text">
          <input
            type="checkbox"
            checked={overlays.changeHeatmap}
            onChange={(e) => onChange({ ...overlays, changeHeatmap: e.target.checked })}
            className="rounded text-amber-400"
          />
          <span>Change Highlights</span>
        </label>
      )}
    </div>
  );
};
