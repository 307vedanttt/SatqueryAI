import React, { useRef, useState } from 'react';
import type { InputConfiguration, UploadedFileInfo } from '../../types';
import { ConfigurationSelector } from './ConfigurationSelector';

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
    roleTitle: string,
    roleBadge: string,
    roleSubtitle: string,
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
            ? 'bg-[#0f172a] border-cyan-500/40 shadow-sm'
            : 'bg-[#0a101d] border-slate-800 hover:border-slate-700 hover:bg-[#0c1322] border-dashed'
        }`}
        onDragOver={handleDragOver}
        onDrop={(e) => handleDropSlot(e, slotIndex)}
      >
        {/* Slot Header */}
        <div className="flex justify-between items-center mb-2.5">
          <div className="flex items-center gap-2">
            <span className="text-sm">{icon}</span>
            <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-slate-200">
              {roleTitle}
            </span>
            <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800 text-cyan-400 font-semibold uppercase">
              {roleBadge}
            </span>
          </div>

          {file && (
            <button
              type="button"
              onClick={() => onRemoveFile(slotIndex)}
              className="text-slate-400 hover:text-red-400 text-[11px] font-mono px-1.5 py-0.5 rounded hover:bg-slate-800/80 transition-colors cursor-pointer"
              title="Remove imagery"
            >
              ✕ Remove
            </button>
          )}
        </div>

        {file ? (
          /* File Loaded Summary */
          <div className="flex items-center gap-3 my-1 p-2 rounded-lg bg-[#070d18] border border-slate-800/80">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt={file.name}
                className="w-12 h-12 rounded-md object-cover border border-slate-700 shrink-0"
              />
            ) : (
              <div className="w-12 h-12 rounded-md bg-[#0d1627] border border-cyan-500/30 flex flex-col items-center justify-center shrink-0">
                <span className="text-sm">🛰️</span>
                <span className="text-[8px] font-mono text-cyan-400 font-bold uppercase">GeoTIFF</span>
              </div>
            )}

            <div className="flex-1 min-w-0">
              <div className="font-semibold text-xs text-slate-100 truncate" title={file.name}>
                {file.name}
              </div>
              <div className="text-[10px] font-mono text-slate-400 flex items-center gap-2 mt-1">
                <span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                <span>•</span>
                <span>{info?.metadata?.width ? `${info.metadata.width}×${info.metadata.height}` : '4096×4096'}</span>
                <span>•</span>
                <span className="text-cyan-400 uppercase font-semibold">{info?.metadata?.crs || 'EPSG:4326'}</span>
              </div>
            </div>
          </div>
        ) : (
          /* Empty Drop Zone */
          <div
            className="flex flex-col items-center justify-center py-5 cursor-pointer text-center group"
            onClick={() => inputRef.current?.click()}
          >
            <div className="w-9 h-9 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 group-hover:text-cyan-400 group-hover:border-cyan-500/40 transition-all mb-1.5">
              <span className="text-base">⬆</span>
            </div>
            <span className="text-xs font-semibold text-slate-300 group-hover:text-white transition-colors">
              {roleSubtitle}
            </span>
            <span className="text-[10px] text-slate-500 mt-1 font-mono">
              GeoTIFF · TIFF · PNG · JPG · Max 100 MB
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
            <span className="text-emerald-400 flex items-center gap-1 font-semibold">
              <span>✓</span> Validated
            </span>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="text-cyan-400 hover:text-cyan-300 hover:underline cursor-pointer"
            >
              Replace File
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="mode-aware-uploader flex flex-col gap-4">
      {/* 3 Configuration Selector Cards */}
      <ConfigurationSelector
        selectedMode={mode}
        onSelectMode={onModeChange}
        disabled={isUploading}
      />

      {/* Upload Drop Slots for Active Configuration */}
      <div className="flex flex-col gap-2">
        <div className="flex justify-between items-center px-1">
          <div className="flex items-center gap-2">
            <label className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <span className="text-cyan-400">📤</span>
              <span>Upload Satellite Imagery</span>
            </label>
            {isDual && files.length === 2 && (
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5 rounded font-semibold flex items-center gap-1">
                <span>✓</span> Co-registration Aligned
              </span>
            )}
          </div>

          {files.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-slate-400">
                {files.length} {files.length === 1 ? 'file' : 'files'} loaded
              </span>
              <button
                type="button"
                onClick={onClearAll}
                className="text-[10px] font-mono text-slate-400 hover:text-red-400 px-2 py-0.5 rounded bg-slate-800/60 border border-slate-700/60 hover:bg-slate-800 transition-colors cursor-pointer"
              >
                Clear All
              </button>
            </div>
          )}
        </div>

        <div className={`grid gap-3 ${isDual ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1'}`}>
          {mode === 'single' && (
            renderSlot(
              0,
              'Satellite Scene',
              'Optical / SAR',
              'Drag & drop imagery here or browse files',
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
                'Optical Sensor',
                'RGB / NIR',
                'Upload Sentinel-2 or Optical Image',
                '🛰️',
                file1,
                info1,
                fileInputRef1
              )}
              {renderSlot(
                1,
                'SAR Sensor',
                'VV / VH Radar',
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
                'T1 — Pre-Event Baseline',
                'Earlier Date',
                'Upload Baseline Acquisition (T1)',
                '⏱️',
                file1,
                info1,
                fileInputRef1
              )}
              {renderSlot(
                1,
                'T2 — Post-Event Target',
                'Later Date',
                'Upload Comparison Acquisition (T2)',
                '⏱️',
                file2,
                info2,
                fileInputRef2
              )}
            </>
          )}
        </div>
      </div>

      {/* Ingestion Loading Status */}
      {isUploading && (
        <div className="p-2.5 rounded-lg bg-blue-950/30 border border-blue-800/40 flex items-center gap-2.5 text-xs font-mono text-cyan-300">
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
            <span className="text-slate-500 hover:text-slate-300">{showDetails ? '▲ Hide Details' : '▼ View Details'}</span>
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
                    <div>CRS: <span className="text-slate-200 font-semibold truncate block">{item.metadata?.crs || 'EPSG:4326'}</span></div>
                    <div>Dimensions: <span className="text-slate-200 font-semibold">{item.metadata?.width ? `${item.metadata.width}×${item.metadata.height} px` : '4096×4096 px'}</span></div>
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
