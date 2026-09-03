import React from 'react';
import type { InputConfiguration, UploadedFileInfo } from '../../types';

interface ConfigurationCardProps {
  files: UploadedFileInfo[];
  configuration?: InputConfiguration;
}

export const ConfigurationCard: React.FC<ConfigurationCardProps> = ({ files, configuration }) => {
  if (files.length === 0) return null;

  // Infer configuration if not provided yet
  let config: InputConfiguration = configuration || 'UNKNOWN';
  let subLabel = 'Detecting configuration...';
  let badgeColor = 'bg-blue-950 text-blue-400 border-blue-800/40';

  if (!configuration) {
    if (files.length === 1) {
      const isSar = files[0].metadata?.image_type === 'sar';
      config = isSar ? 'SINGLE_SAR' : 'SINGLE_OPTICAL';
    } else if (files.length === 2) {
      const isSar0 = files[0].metadata?.image_type === 'sar';
      const isSar1 = files[1].metadata?.image_type === 'sar';
      if ((isSar0 && !isSar1) || (!isSar0 && isSar1)) {
        config = 'OPTICAL_SAR_PAIR';
      } else {
        config = 'BI_TEMPORAL';
      }
    }
  }

  switch (config) {
    case 'SINGLE_OPTICAL':
      subLabel = 'Single multispectral / optical scene';
      badgeColor = 'bg-blue-950 text-blue-300 border-blue-800/40';
      break;
    case 'SINGLE_SAR':
      subLabel = 'Single Synthetic Aperture Radar intensity raster';
      badgeColor = 'bg-purple-950 text-purple-300 border-purple-800/40';
      break;
    case 'OPTICAL_SAR_PAIR':
      subLabel = 'Complementary cross-modal sensor pair';
      badgeColor = 'bg-cyan-950 text-cyan-300 border-cyan-800/40';
      break;
    case 'BI_TEMPORAL':
      subLabel = '2 co-registered temporal acquisition dates';
      badgeColor = 'bg-emerald-950 text-emerald-300 border-emerald-800/40';
      break;
    default:
      subLabel = 'Awaiting sufficient imagery for configuration classification';
      badgeColor = 'bg-surface-2 text-text-3 border-glass-border';
  }

  const formattedName = config.replace(/_/g, ' ');

  return (
    <div className="card p-3 bg-surface rounded-xl border border-glass-border">
      <div className="text-[10px] font-mono text-text-3 uppercase tracking-wider mb-1">
        DETECTED CONFIGURATION
      </div>

      <div className="flex items-center justify-between gap-2">
        <span className={`font-mono font-bold text-xs px-2 py-0.5 rounded border ${badgeColor}`}>
          {formattedName}
        </span>
        <span className="text-[11px] font-mono text-text-3">
          {files.length} {files.length === 1 ? 'image' : 'images'}
        </span>
      </div>

      <div className="text-xs text-text-2 mt-1.5 leading-relaxed">
        {subLabel}
      </div>
    </div>
  );
};
