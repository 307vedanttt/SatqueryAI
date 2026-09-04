import React, { useRef, useState } from 'react';
import type { InputConfiguration, UploadedFileInfo } from '../../types';
import { ConfigurationSelector } from './ConfigurationSelector';

export type AnalysisMode = 'single' | 'grounding' | 'optical-sar' | 'bi-temporal';

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
    icon: React.ReactNode,
    file: File | null,
    info: UploadedFileInfo | null,
    inputRef: React.RefObject<HTMLInputElement | null>
  ) => {
    const isGeoTIFF = file?.name.toLowerCase().endsWith('.tif') || file?.name.toLowerCase().endsWith('.tiff');
    const previewUrl = file && !isGeoTIFF ? URL.createObjectURL(file) : null;
    const fileExtension = file ? (file.name.split('.').pop() || 'file').toUpperCase() : '';
    const fileType = isGeoTIFF ? 'GeoTIFF' : fileExtension;

    const dimensionsText = info?.metadata?.width
      ? `${info.metadata.width} × ${info.metadata.height} px`
      : '4096 × 4096 px';
    const bandsText = info?.metadata?.bands ? `${info.metadata.bands} Bands` : '4 Bands';
    const crsText = info?.metadata?.crs || 'EPSG:4326';
    const sensorText = info?.metadata?.sensor || (roleBadge.includes('SAR') ? 'Sentinel-1 SAR' : 'Sentinel-2 MSI');

    return (
      <div
        className={`relative flex-1 rounded-xl transition-all duration-200 p-3.5 flex flex-col justify-between border ${
          file
            ? 'bg-slate-900/90 border-cyan-500/40 shadow-lg shadow-cyan-950/30 backdrop-blur-md'
            : 'bg-slate-950/60 border-white/10 hover:border-cyan-500/40 hover:bg-slate-900/50 backdrop-blur-md border-dashed'
        }`}
        onDragOver={handleDragOver}
        onDrop={(e) => handleDropSlot(e, slotIndex)}
      >
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

        {file ? (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="p-1 rounded bg-slate-950 border border-white/10 text-cyan-400">
                  {icon}
                </span>
                <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-200">
                  {roleTitle}
                </span>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/40 text-cyan-300 font-semibold uppercase">
                  {roleBadge}
                </span>
              </div>

              <span className="px-2 py-0.5 rounded-md font-mono text-[10px] font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-500/50 flex items-center gap-1 shadow-sm">
                <svg className="w-3 h-3 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                VALIDATED
              </span>
            </div>

            <div className="flex items-center gap-3 p-2.5 rounded-lg bg-slate-950/70 border border-white/5">
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt={file.name}
                  className="w-11 h-11 rounded-md object-cover border border-white/10 shrink-0 shadow-sm"
                />
              ) : (
                <div className="w-11 h-11 rounded-md bg-slate-900 border border-cyan-500/30 flex flex-col items-center justify-center shrink-0 text-cyan-400 shadow-sm">
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <polygon points="12 2 2 7 12 12 22 7 12 2" />
                    <polyline points="2 17 12 22 22 17" />
                    <polyline points="2 12 17 22 12" />
                  </svg>
                  <span className="text-[8px] font-mono text-cyan-400 font-bold uppercase mt-0.5">
                    {fileType}
                  </span>
                </div>
              )}

              <div className="flex-1 min-w-0">
                <div className="font-bold text-xs text-white truncate" title={file.name}>
                  {file.name}
                </div>
                <div className="text-[10px] font-mono text-slate-400 flex items-center gap-2 mt-0.5">
                  <span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                  <span>•</span>
                  <span className="text-slate-200 font-semibold">{fileType}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-2 rounded-lg bg-slate-950/50 border border-white/5 font-mono text-[10px]">
              <div className="flex flex-col">
                <span className="text-slate-500 text-[9px]">DIMENSIONS</span>
                <span className="text-slate-200 font-bold">{dimensionsText}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-500 text-[9px]">BANDS</span>
                <span className="text-slate-200 font-bold">{bandsText}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-500 text-[9px]">CRS</span>
                <span className="text-cyan-300 font-bold">{crsText}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-500 text-[9px]">SENSOR</span>
                <span className="text-slate-200 font-bold truncate">{sensorText}</span>
              </div>
            </div>

            <div className="flex justify-between items-center pt-1 text-[11px] font-mono">
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                className="px-2.5 py-1 rounded bg-slate-800/80 hover:bg-slate-700 text-cyan-300 hover:text-white border border-white/10 transition-all cursor-pointer flex items-center gap-1 font-semibold text-[10px]"
              >
                <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 2v6h-6" />
                  <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
                  <path d="M3 22v-6h6" />
                  <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
                </svg>
                Replace
              </button>

              <button
                type="button"
                onClick={() => onRemoveFile(slotIndex)}
                className="px-2.5 py-1 rounded bg-slate-900 hover:bg-rose-950/80 text-slate-400 hover:text-rose-300 border border-white/10 hover:border-rose-800/60 transition-all cursor-pointer flex items-center gap-1 font-semibold text-[10px]"
              >
                <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
                Remove
              </button>
            </div>
          </div>
        ) : (
          <div
            className="flex flex-col items-center justify-center py-6 px-4 cursor-pointer text-center group"
            onClick={() => inputRef.current?.click()}
          >
            <div className="w-10 h-10 rounded-xl bg-slate-900 border border-white/10 flex items-center justify-center text-slate-400 group-hover:text-cyan-400 group-hover:border-cyan-500/40 transition-all mb-2 shadow-sm">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <div className="font-mono text-xs font-bold text-slate-200 group-hover:text-cyan-300 transition-colors uppercase tracking-wider mb-1">
              UPLOAD SATELLITE IMAGERY
            </div>
            <span className="text-xs font-semibold text-slate-300 group-hover:text-white transition-colors">
              {roleSubtitle}
            </span>
            <span className="text-[10px] text-slate-400 mt-1.5 font-mono">
              GeoTIFF · TIFF · PNG · JPG · Max 100 MB
            </span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="mode-aware-uploader flex flex-col gap-4">
      <ConfigurationSelector
        selectedMode={mode}
        onSelectMode={onModeChange}
        disabled={isUploading}
      />

      <div className="flex flex-col gap-2">
        <div className="flex justify-between items-center px-1">
          <div className="flex items-center gap-2">
            <label className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <span className="text-cyan-400">📤</span>
              <span>UPLOAD WORKSPACE</span>
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
              (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M13 2L3 12" />
                  <path d="M7 2L2 7" />
                  <path d="M22 17L17 22" />
                  <path d="M22 13L13 22" />
                  <path d="M8 8l8 8" />
                </svg>
              ),
              file1,
              info1,
              fileInputRef1
            )
          )}

          {mode === 'grounding' && (
            renderSlot(
              0,
              'Grounding Target Scene',
              'Localization',
              'Upload imagery for target localization & bounding box detection',
              (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <circle cx="12" cy="12" r="9" />
                  <circle cx="12" cy="12" r="3" />
                  <line x1="12" y1="2" x2="12" y2="5" />
                  <line x1="12" y1="19" x2="12" y2="22" />
                  <line x1="2" y1="12" x2="5" y2="12" />
                  <line x1="19" y1="12" x2="22" y2="12" />
                </svg>
              ),
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
                (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <polygon points="12 2 2 7 12 12 22 7 12 2" />
                    <polyline points="2 17 12 22 22 17" />
                    <polyline points="2 12 17 22 12" />
                  </svg>
                ),
                file1,
                info1,
                fileInputRef1
              )}
              {renderSlot(
                1,
                'SAR Sensor',
                'VV / VH Radar',
                'Upload Sentinel-1 SAR Intensity Raster',
                (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9" />
                    <path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5" />
                    <circle cx="12" cy="12" r="2" />
                    <path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5" />
                    <path d="M19.1 4.9c3.9 3.9 3.9 10.3 0 14.2" />
                  </svg>
                ),
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
                (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <circle cx="12" cy="12" r="9" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                ),
                file1,
                info1,
                fileInputRef1
              )}
              {renderSlot(
                1,
                'T2 — Post-Event Target',
                'Later Date',
                'Upload Comparison Acquisition (T2)',
                (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <circle cx="12" cy="12" r="9" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                ),
                file2,
                info2,
                fileInputRef2
              )}
            </>
          )}
        </div>
      </div>

      {isUploading && (
        <div className="p-3 rounded-xl bg-cyan-950/40 border border-cyan-500/40 flex items-center gap-3 text-xs font-mono text-cyan-300 shadow-md backdrop-blur-md">
          <span className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin shrink-0" />
          <span className="font-semibold">Ingesting raster, extracting metadata & verifying spatial bounds...</span>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs font-mono text-rose-300 flex items-center gap-2 shadow-md backdrop-blur-md">
          <svg className="w-4 h-4 text-rose-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {files.length > 0 && (
        <div className="rounded-xl border border-white/10 bg-slate-950/70 backdrop-blur-xl overflow-hidden shadow-lg">
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="w-full px-3.5 py-2 flex justify-between items-center text-xs font-mono font-semibold text-slate-300 hover:text-white hover:bg-white/5 transition-colors cursor-pointer select-none"
          >
            <div className="flex items-center gap-2">
              <span className="text-cyan-400 font-sans">📋</span>
              <span>GEOSPATIAL & METADATA DETAILS</span>
              {detectedConfiguration && (
                <span className="px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/50 text-[10px]">
                  {detectedConfiguration}
                </span>
              )}
            </div>
            <span className="text-slate-500 hover:text-slate-300">{showDetails ? '▲ Hide Details' : '▼ View Details'}</span>
          </button>

          {showDetails && (
            <div className="p-3.5 border-t border-white/10 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono bg-slate-950/90">
              {uploadedInfos.map((item, idx) => (
                <div key={idx} className="space-y-2 p-3 rounded-lg bg-slate-900/80 border border-white/5">
                  <div className="text-[11px] font-bold text-cyan-400 truncate" title={item.original_filename}>
                    Slot {idx + 1}: {item.original_filename}
                  </div>
                  <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] text-slate-400">
                    <div>Format: <span className="text-slate-200 font-semibold">{item.extension.toUpperCase()}</span></div>
                    <div>GeoTIFF: <span className="text-slate-200 font-semibold">{item.is_geotiff ? 'Yes' : 'No'}</span></div>
                    <div>Sensor: <span className="text-slate-200 font-semibold">{item.metadata?.sensor || 'Optical'}</span></div>
                    <div>Resolution: <span className="text-slate-200 font-semibold">{item.metadata?.resolution ? `${item.metadata.resolution[0]}m` : '10m GSD'}</span></div>
                    <div>CRS: <span className="text-slate-200 font-semibold truncate block">{item.metadata?.crs || 'EPSG:4326'}</span></div>
                    <div>Dimensions: <span className="text-slate-200 font-semibold">{item.metadata?.width ? `${item.metadata.width} × ${item.metadata.height} px` : '4096 × 4096 px'}</span></div>
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
