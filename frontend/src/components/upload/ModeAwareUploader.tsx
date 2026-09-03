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

  const renderSlot = (
    slotIndex: number,
    label: string,
    subLabel: string,
    icon: string,
    file: File | null,
    info: UploadedFileInfo | null,
    inputRef: React.RefObject<HTMLInputElement | null>
  ) => {
    const isGeoTIFF = file?.name.toLowerCase().endsWith('.tif') || file?.name.toLowerCase().endsWith('.tiff');
    const previewUrl = file && !isGeoTIFF ? URL.createObjectURL(file) : null;

    return (
      <div
        className={`relative flex-1 rounded-xl transition-all p-3.5 flex flex-col justify-between border ${
          file
            ? 'bg-[#111c30] border-blue-500/40 shadow-sm'
            : 'bg-[#0b1220]/60 border-slate-800 hover:border-slate-700 hover:bg-[#0e1626]/80 border-dashed'
        }`}
        onDragOver={handleDragOver}
        onDrop={(e) => handleDropSlot(e, slotIndex)}
      >
        <div className="flex justify-between items-center mb-2.5">
          <div className="flex items-center gap-2">
            <span className="text-sm">{icon}</span>
            <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-slate-200">
              {label}
            </span>
          </div>

          {file && (
            <button
              type="button"
              onClick={() => onRemoveFile(slotIndex)}
              className="text-slate-400 hover:text-red-400 text-[11px] font-mono px-2 py-0.5 rounded hover:bg-slate-800/80 transition-colors cursor-pointer"
              title="Remove this imagery"
            >
              ✕ Remove
            </button>
          )}
        </div>

        {file ? (
          /* File Loaded Card */
          <div className="flex items-center gap-3 my-1 p-2 rounded-lg bg-[#0a101d] border border-slate-800/80">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt={file.name}
                className="w-12 h-12 rounded-md object-cover border border-slate-700 shrink-0"
              />
            ) : (
              <div className="w-12 h-12 rounded-md bg-[#0d1627] border border-blue-500/30 flex flex-col items-center justify-center shrink-0">
                <span className="text-base">🛰️</span>
                <span className="text-[9px] font-mono text-cyan-400 font-bold uppercase">TIFF</span>
              </div>
            )}

            <div className="flex-1 min-w-0">
              <div className="font-semibold text-xs text-slate-100 truncate" title={file.name}>
                {file.name}
              </div>
              <div className="text-[10px] font-mono text-slate-400 flex items-center gap-2 mt-1">
                <span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                <span>•</span>
                <span className="px-1.5 py-0.2 rounded bg-blue-950/80 text-blue-300 border border-blue-800/40 uppercase font-semibold">
                  {info?.metadata?.image_type || (isGeoTIFF ? 'GeoTIFF' : 'Raster')}
                </span>
              </div>
            </div>
          </div>
        ) : (
          /* Empty Drop Zone */
          <div
            className="flex flex-col items-center justify-center py-5 cursor-pointer text-center group"
            onClick={() => inputRef.current?.click()}
          >
            <div className="w-10 h-10 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 group-hover:text-cyan-400 group-hover:border-cyan-500/40 transition-all mb-2">
              <span className="text-lg">⬆</span>
            </div>
            <span className="text-xs font-semibold text-slate-300 group-hover:text-white transition-colors">
              {subLabel}
            </span>
            <span className="text-[10px] text-slate-500 mt-1 font-mono">
              GeoTIFF (.tif), PNG, JPG up to 100MB
            </span>
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
          <div className="pt-2 mt-2 border-t border-slate-800/60 flex justify-between items-center text-[10px] font-mono">
            <span className="text-emerald-400 flex items-center gap-1">
              <span>✓</span> Ingested & Validated
            </span>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="text-cyan-400 hover:text-cyan-300 hover:underline cursor-pointer"
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
      {/* Segmented Mode Selector Switch */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-1.5 rounded-xl bg-[#0c1322] border border-slate-800/80">
        <div className="flex items-center gap-1">
          <button
            type="button"
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
              mode === 'single'
                ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
            onClick={() => onModeChange('single')}
          >
            <span>🛰️</span>
            <span>Single Scene</span>
          </button>

          <button
            type="button"
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
              mode === 'optical-sar'
                ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
            onClick={() => onModeChange('optical-sar')}
          >
            <span>📡</span>
            <span>Optical + SAR Pair</span>
          </button>

          <button
            type="button"
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
              mode === 'bi-temporal'
                ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
            onClick={() => onModeChange('bi-temporal')}
          >
            <span>⏱️</span>
            <span>Bi-Temporal Change</span>
          </button>
        </div>

        {files.length > 0 && (
          <div className="flex items-center gap-2 pr-1">
            <span className="text-[11px] font-mono text-slate-400">
              {files.length} {files.length === 1 ? 'file' : 'files'} active
            </span>
            <button
              type="button"
              onClick={onClearAll}
              className="text-[10px] font-mono text-slate-400 hover:text-red-400 px-2 py-0.5 rounded bg-slate-800/60 border border-slate-700/60 hover:bg-slate-800 transition-colors cursor-pointer"
            >
              Reset All
            </button>
          </div>
        )}
      </div>

      {/* Upload Drop Slots */}
      <div className={`grid gap-3 ${isDual ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1'}`}>
        {mode === 'single' && (
          renderSlot(
            0,
            'Satellite Scene',
            'Click or drop satellite imagery here',
            '🛰️',
            file1,
            info1,
            fileInputRef1
          )
        )}

        {mode === 'optical-sar' && (
          <>
            {renderSlot(
              0,
              'Optical Sensor (Multispectral)',
              'Upload Sentinel-2 or Optical Scene',
              '🛰️',
              file1,
              info1,
              fileInputRef1
            )}
            {renderSlot(
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
            {renderSlot(
              0,
              'T1 — Pre-Event Baseline (Before)',
              'Upload Initial Acquisition (T1)',
              '⏱️',
              file1,
              info1,
              fileInputRef1
            )}
            {renderSlot(
              1,
              'T2 — Post-Event Target (After)',
              'Upload Comparison Acquisition (T2)',
              '⏱️',
              file2,
              info2,
              fileInputRef2
            )}
          </>
        )}
      </div>

      {/* Ingestion Loading Status */}
      {isUploading && (
        <div className="p-2.5 rounded-lg bg-blue-950/30 border border-blue-800/40 flex items-center gap-2.5 text-xs font-mono text-blue-300">
          <span className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin shrink-0" />
          <span>Ingesting raster, extracting metadata & verifying spatial bounds...</span>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="p-2.5 rounded-lg bg-red-950/30 border border-red-800/40 text-xs font-mono text-red-300 flex items-center gap-2">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Expandable Geospatial Metadata Drawer */}
      {files.length > 0 && (
        <div className="rounded-xl border border-slate-800 bg-[#0d1424] overflow-hidden">
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="w-full px-3.5 py-2 flex justify-between items-center text-xs font-mono font-semibold text-slate-300 hover:text-white hover:bg-slate-800/50 transition-colors cursor-pointer select-none"
          >
            <div className="flex items-center gap-2">
              <span className="text-cyan-400">📋</span>
              <span>GEOSPATIAL & METADATA DETAILS</span>
              {detectedConfiguration && (
                <span className="px-1.5 py-0.2 rounded bg-blue-950 text-cyan-300 border border-blue-800/50 text-[10px]">
                  {detectedConfiguration}
                </span>
              )}
            </div>
            <span className="text-slate-500 hover:text-slate-300">{showDetails ? '▲ Hide' : '▼ View'}</span>
          </button>

          {showDetails && (
            <div className="p-3.5 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono bg-[#090f1a]">
              {uploadedInfos.map((item, idx) => (
                <div key={idx} className="space-y-2 p-3 rounded-lg bg-[#0e1627] border border-slate-800">
                  <div className="text-[11px] font-bold text-cyan-400 truncate" title={item.original_filename}>
                    Slot {idx + 1}: {item.original_filename}
                  </div>
                  <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] text-slate-400">
                    <div>Format: <span className="text-slate-200 font-semibold">{item.extension.toUpperCase()}</span></div>
                    <div>GeoTIFF: <span className="text-slate-200 font-semibold">{item.is_geotiff ? 'Yes' : 'No'}</span></div>
                    <div>Sensor: <span className="text-slate-200 font-semibold">{item.metadata?.sensor || 'Optical'}</span></div>
                    <div>Resolution: <span className="text-slate-200 font-semibold">{item.metadata?.resolution ? `${item.metadata.resolution[0]}m` : '10m GSD'}</span></div>
                    <div>CRS: <span className="text-slate-200 font-semibold truncate block">{item.metadata?.crs || 'EPSG:32643'}</span></div>
                    <div>Dimensions: <span className="text-slate-200 font-semibold">{item.metadata?.width ? `${item.metadata.width}×${item.metadata.height} px` : '1920×1080 px'}</span></div>
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
