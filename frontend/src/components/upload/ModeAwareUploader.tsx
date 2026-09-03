import React, { useRef, useState } from 'react';
import type { InputConfiguration, UploadedFileInfo } from '../../types';

export type AnalysisMode = 'single' | 'optical-sar' | 'bi-temporal';

interface ModeAwareUploaderProps {
  mode: AnalysisMode;
  onModeChange: (mode: AnalysisMode) => void;
  files: File[];
  uploadedInfos: UploadedFileInfo[];
  onFilesSelected: (files: File[]) => void;
  onReplaceFile: (slotIndex: number, file: File) => void;
  onRemoveFile: (slotIndex: number) => void;
  onClearAll: () => void;
  isUploading: boolean;
  error?: string | null;
  detectedConfiguration?: InputConfiguration;
}

export const ModeAwareUploader: React.FC<ModeAwareUploaderProps> = ({
  mode,
  onModeChange,
  files,
  uploadedInfos,
  onFilesSelected,
  onReplaceFile,
  onRemoveFile,
  onClearAll,
  isUploading,
  error,
  detectedConfiguration,
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const fileInputRef1 = useRef<HTMLInputElement>(null);
  const fileInputRef2 = useRef<HTMLInputElement>(null);

  const isDual = mode === 'optical-sar' || mode === 'bi-temporal';

  // Slot 1 & 2 file states
  const file1 = files[0] || null;
  const file2 = files[1] || null;
  const info1 = uploadedInfos[0] || null;
  const info2 = uploadedInfos[1] || null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDropSlot = (e: React.DragEvent, slotIndex: number) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const dropped = e.dataTransfer.files[0];
      if (files.length === 0 && slotIndex === 0) {
        onFilesSelected([dropped]);
      } else {
        onReplaceFile(slotIndex, dropped);
      }
    }
  };

  const renderSlotUploader = (
    slotIndex: number,
    title: string,
    subtitle: string,
    icon: string,
    file: File | null,
    info: UploadedFileInfo | null,
    inputRef: React.RefObject<HTMLInputElement | null>
  ) => {
    const isGeoTIFF = file?.name.toLowerCase().endsWith('.tif') || file?.name.toLowerCase().endsWith('.tiff');
    const previewUrl = file && !isGeoTIFF ? URL.createObjectURL(file) : null;

    return (
      <div
        className={`slot-uploader flex-1 rounded-xl border transition-all p-3 flex flex-col justify-between ${
          file
            ? 'bg-surface-2/70 border-blue-500/50'
            : 'bg-surface/60 border-glass-border hover:border-blue-400/60 border-dashed'
        }`}
        onDragOver={handleDragOver}
        onDrop={(e) => handleDropSlot(e, slotIndex)}
      >
        <div className="flex justify-between items-center mb-2">
          <div className="flex items-center gap-1.5">
            <span className="text-base">{icon}</span>
            <span className="font-mono text-xs font-bold uppercase text-text tracking-wider">
              {title}
            </span>
          </div>

          {file && (
            <button
              type="button"
              onClick={() => onRemoveFile(slotIndex)}
              className="text-text-3 hover:text-red-400 text-xs font-mono px-1.5 py-0.5 rounded hover:bg-surface-3 transition-colors cursor-pointer"
              title="Remove file"
            >
              ✕ Remove
            </button>
          )}
        </div>

        {file ? (
          /* Uploaded File Summary */
          <div className="flex items-center gap-3 my-1">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt={file.name}
                className="w-12 h-12 rounded object-cover border border-glass-border shrink-0"
              />
            ) : (
              <div className="w-12 h-12 rounded bg-[#0a1424] border border-blue-900/50 flex flex-col items-center justify-center shrink-0">
                <span className="text-lg">🛰️</span>
                <span className="text-[9px] font-mono text-blue-400 font-bold">TIFF</span>
              </div>
            )}

            <div className="flex-1 min-w-0">
              <div className="font-bold text-xs text-text truncate" title={file.name}>
                {file.name}
              </div>
              <div className="text-[10px] font-mono text-text-3 flex gap-2 mt-0.5">
                <span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                <span>•</span>
                <span className="text-blue-300 uppercase">{info?.metadata?.image_type || 'Optical'}</span>
              </div>
            </div>
          </div>
        ) : (
          /* Empty Drop Zone */
          <div
            className="flex flex-col items-center justify-center py-4 cursor-pointer text-center"
            onClick={() => inputRef.current?.click()}
          >
            <span className="text-2xl mb-1 opacity-50">📤</span>
            <span className="text-xs text-text font-medium">{subtitle}</span>
            <span className="text-[10px] text-text-3 mt-0.5">Drop GeoTIFF, TIFF, PNG, or JPG</span>
          </div>
        )}

        <input
          ref={inputRef as React.RefObject<HTMLInputElement>}
          type="file"
          accept=".tif,.tiff,.png,.jpg,.jpeg"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              if (slotIndex === 0 && files.length === 0) {
                onFilesSelected([e.target.files[0]]);
              } else {
                onReplaceFile(slotIndex, e.target.files[0]);
              }
            }
          }}
        />

        {file && (
          <div className="pt-2 border-t border-glass-border/40 flex justify-between items-center text-[10px] font-mono text-text-3">
            <span>Status: <strong className="text-emerald-400">Validated ✓</strong></span>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="text-accent hover:underline cursor-pointer"
            >
              Replace
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="mode-aware-uploader flex flex-col gap-3">
      {/* Mode Selector Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-1.5 rounded-xl bg-surface border border-glass-border">
        <div className="flex items-center gap-1">
          <button
            type="button"
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
              mode === 'single'
                ? 'bg-blue-600 text-white shadow'
                : 'text-text-3 hover:text-text hover:bg-surface-2'
            }`}
            onClick={() => onModeChange('single')}
          >
            <span>🛰️</span>
            <span>Single Image</span>
          </button>

          <button
            type="button"
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
              mode === 'optical-sar'
                ? 'bg-blue-600 text-white shadow'
                : 'text-text-3 hover:text-text hover:bg-surface-2'
            }`}
            onClick={() => onModeChange('optical-sar')}
          >
            <span>📡</span>
            <span>Optical + SAR</span>
          </button>

          <button
            type="button"
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
              mode === 'bi-temporal'
                ? 'bg-blue-600 text-white shadow'
                : 'text-text-3 hover:text-text hover:bg-surface-2'
            }`}
            onClick={() => onModeChange('bi-temporal')}
          >
            <span>⏱️</span>
            <span>Bi-Temporal Change</span>
          </button>
        </div>

        {files.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-text-3">
              {files.length} {files.length === 1 ? 'file' : 'files'} loaded
            </span>
            <button
              type="button"
              onClick={onClearAll}
              className="text-[11px] font-mono text-text-3 hover:text-red-400 px-2 py-0.5 rounded bg-surface-2 border border-glass-border transition-colors cursor-pointer"
            >
              Clear All
            </button>
          </div>
        )}
      </div>

      {/* Upload Drop Slots */}
      <div className={`grid gap-3 ${isDual ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1'}`}>
        {mode === 'single' && (
          renderSlotUploader(
            0,
            'Satellite Scene',
            'Click or drop image to upload',
            '🛰️',
            file1,
            info1,
            fileInputRef1
          )
        )}

        {mode === 'optical-sar' && (
          <>
            {renderSlotUploader(
              0,
              'Optical Sensor (T1)',
              'Upload Multispectral / Optical Image',
              '🛰️',
              file1,
              info1,
              fileInputRef1
            )}
            {renderSlotUploader(
              1,
              'SAR Sensor (Radar)',
              'Upload Sentinel-1 SAR Intensity Raster',
              '📡',
              file2,
              info2,
              fileInputRef2
            )}
          </>
        )}

        {mode === 'bi-temporal' && (
          <>
            {renderSlotUploader(
              0,
              'T1 — Pre-Event / Before',
              'Upload Baseline Acquisition (T1)',
              '⏱️',
              file1,
              info1,
              fileInputRef1
            )}
            {renderSlotUploader(
              1,
              'T2 — Post-Event / After',
              'Upload Comparison Acquisition (T2)',
              '⏱️',
              file2,
              info2,
              fileInputRef2
            )}
          </>
        )}
      </div>

      {/* Uploading Status indicator */}
      {isUploading && (
        <div className="p-2.5 rounded-lg bg-blue-950/40 border border-blue-800/40 flex items-center gap-2 text-xs font-mono text-blue-300">
          <span className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          <span>Ingesting raster & validating geospatial parameters...</span>
        </div>
      )}

      {/* Error message if upload fails */}
      {error && (
        <div className="p-2.5 rounded-lg bg-red-950/40 border border-red-800/40 text-xs font-mono text-red-300 flex items-center gap-2">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Expandable Image Details Disclosure */}
      {files.length > 0 && (
        <div className="rounded-xl border border-glass-border bg-surface overflow-hidden">
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="w-full px-3 py-2 flex justify-between items-center text-xs font-mono font-semibold text-text hover:bg-surface-2 transition-colors cursor-pointer select-none"
          >
            <div className="flex items-center gap-2">
              <span>📋</span>
              <span>GEOSPATIAL & METADATA DETAILS</span>
              {detectedConfiguration && (
                <span className="px-1.5 py-0.2 rounded bg-blue-950 text-blue-300 border border-blue-800/40 text-[10px]">
                  {detectedConfiguration}
                </span>
              )}
            </div>
            <span className="text-text-3">{showDetails ? '▲ Hide' : '▼ View Details'}</span>
          </button>

          {showDetails && (
            <div className="p-3 border-t border-glass-border/40 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono text-text-2 bg-surface-2/40">
              {uploadedInfos.map((item, idx) => (
                <div key={idx} className="space-y-1.5 p-2.5 rounded-lg bg-surface border border-glass-border/50">
                  <div className="text-[11px] font-bold text-accent truncate" title={item.original_filename}>
                    Slot {idx + 1}: {item.original_filename}
                  </div>
                  <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] text-text-3">
                    <div>Format: <span className="text-text">{item.extension.toUpperCase()}</span></div>
                    <div>GeoTIFF: <span className="text-text">{item.is_geotiff ? 'Yes' : 'No'}</span></div>
                    <div>Sensor: <span className="text-text">{item.metadata?.sensor || 'Optical'}</span></div>
                    <div>Resolution: <span className="text-text">{item.metadata?.resolution ? `${item.metadata.resolution[0]}m` : '10m'}</span></div>
                    <div>CRS: <span className="text-text truncate block">{item.metadata?.crs || 'EPSG:32643'}</span></div>
                    <div>Dimensions: <span className="text-text">{item.metadata?.width ? `${item.metadata.width}x${item.metadata.height}` : 'N/A'}</span></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
