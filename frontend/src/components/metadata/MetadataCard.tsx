import React from 'react';
import type { UploadedFileInfo } from '../../types';

interface MetadataCardProps {
  files: UploadedFileInfo[];
  selectedFileIndex?: number;
  onSelectFileIndex?: (index: number) => void;
}

export const MetadataCard: React.FC<MetadataCardProps> = ({
  files,
  selectedFileIndex = 0,
  onSelectFileIndex,
}) => {
  if (files.length === 0) return null;

  const currentFile = files[selectedFileIndex] || files[0];
  const meta = currentFile?.metadata;

  return (
    <div className="card p-3 bg-surface rounded-xl border border-glass-border">
      <div className="flex justify-between items-center mb-2">
        <div className="text-xs font-semibold flex items-center gap-1.5 text-text">
          <span>📋</span>
          <span>IMAGE METADATA</span>
        </div>

        {files.length > 1 && onSelectFileIndex && (
          <div className="flex gap-1">
            {files.map((_, idx) => (
              <button
                key={idx}
                type="button"
                className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${
                  selectedFileIndex === idx
                    ? 'bg-blue-600 border-blue-400 text-white'
                    : 'bg-surface-2 border-glass-border text-text-3 hover:text-text'
                }`}
                onClick={() => onSelectFileIndex(idx)}
              >
                T{idx + 1}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="text-[11px] font-medium text-text truncate mb-2" title={currentFile.original_filename}>
        {currentFile.original_filename}
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-2 text-xs font-mono">
        <div>
          <span className="text-[10px] text-text-3 block">SENSOR</span>
          <span className="text-text-2 text-[11px] font-semibold">
            {meta?.sensor || 'Not available'}
          </span>
        </div>

        <div>
          <span className="text-[10px] text-text-3 block">MODALITY TYPE</span>
          <span className="text-text-2 text-[11px] uppercase">
            {meta?.image_type || 'Optical'}
          </span>
        </div>

        <div>
          <span className="text-[10px] text-text-3 block">DIMENSIONS</span>
          <span className="text-text-2 text-[11px]">
            {meta?.width && meta?.height ? `${meta.width} × ${meta.height}` : 'Not available'}
          </span>
        </div>

        <div>
          <span className="text-[10px] text-text-3 block">BANDS</span>
          <span className="text-text-2 text-[11px]">
            {meta?.bands !== null && meta?.bands !== undefined ? `${meta.bands} bands` : 'Not available'}
          </span>
        </div>

        <div>
          <span className="text-[10px] text-text-3 block">RESOLUTION</span>
          <span className="text-text-2 text-[11px]">
            {meta?.resolution ? `${meta.resolution[0]} m` : 'Not available'}
          </span>
        </div>

        <div>
          <span className="text-[10px] text-text-3 block">CRS</span>
          <span className="text-text-2 text-[11px] truncate block" title={meta?.crs || undefined}>
            {meta?.crs || 'Not available'}
          </span>
        </div>

        <div className="col-span-2">
          <span className="text-[10px] text-text-3 block">ACQUISITION DATE</span>
          <span className="text-text-2 text-[11px]">
            {meta?.acquisition_date || 'Not available'}
          </span>
        </div>
      </div>
    </div>
  );
};
