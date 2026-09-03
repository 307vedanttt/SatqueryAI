import React, { useRef, useState } from 'react';
import type { UploadedFileInfo } from '../../types';

interface UploadZoneProps {
  files: File[];
  uploadedInfos: UploadedFileInfo[];
  onFilesSelected: (files: File[]) => void;
  onRemoveFile: (index: number) => void;
  isUploading: boolean;
  error: string | null;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  files,
  uploadedInfos,
  onFilesSelected,
  onRemoveFile,
  isUploading,
  error,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFilesSelected(Array.from(e.dataTransfer.files));
    }
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelected(Array.from(e.target.files));
    }
  };

  return (
    <div className="upload-container flex flex-col gap-3">
      {/* Drag & Drop Box */}
      <div
        className={`upload-zone border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-blue-500 bg-blue-950/20'
            : 'border-glass-border hover:border-blue-400/50 bg-surface/50'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleBrowseClick}
        role="button"
        tabIndex={0}
        aria-label="Upload remote sensing imagery"
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".tif,.tiff,.png,.jpg,.jpeg"
          className="hidden"
          onChange={handleFileChange}
        />

        <div className="text-3xl mb-2" aria-hidden="true">🛰️</div>

        <div className="font-semibold text-sm text-text">
          {isUploading ? 'Reading Imagery & Metadata...' : 'Upload Remote Sensing Imagery'}
        </div>

        <div className="text-xs text-text-3 mt-1">
          Drag & drop files here, or <span className="text-blue-400 underline font-medium">Browse files</span>
        </div>

        <div className="text-[11px] font-mono text-text-3 mt-2 px-2 py-0.5 rounded bg-surface-2 inline-block">
          Supported: GeoTIFF • TIFF • PNG • JPEG
        </div>

        {/* Uploading progress bar */}
        {isUploading && (
          <div className="mt-4 w-full bg-surface-2 h-1.5 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 animate-pulse w-3/4 rounded-full" />
          </div>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div className="error-banner p-3 rounded-lg border border-red-500/30 bg-red-950/20 text-xs text-red-300 flex items-start gap-2">
          <span className="text-base" aria-hidden="true">✕</span>
          <div>
            <strong>Unable to process imagery:</strong> {error}
          </div>
        </div>
      )}

      {/* Uploaded File Cards (Separated into IMAGE 1 and IMAGE 2) */}
      {files.length > 0 && (
        <div className="uploaded-slots flex flex-col gap-2">
          {files.map((file, idx) => {
            const info = uploadedInfos[idx];
            const meta = info?.metadata;
            const slotTitle = files.length > 1 ? `IMAGE ${idx + 1}` : 'IMAGE 1';
            const isGeo = file.name.toLowerCase().endsWith('.tif') || file.name.toLowerCase().endsWith('.tiff');

            return (
              <div
                key={`${file.name}-${idx}`}
                className="uploaded-card p-3 rounded-lg border border-glass-border bg-surface flex justify-between items-start"
              >
                <div className="flex flex-col gap-1 min-w-0 pr-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-[11px] px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/40">
                      {slotTitle}
                    </span>
                    <span className="text-xs font-semibold text-text truncate max-w-[180px]" title={file.name}>
                      {file.name}
                    </span>
                    {isGeo && (
                      <span className="font-mono text-[10px] px-1 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/40">
                        GeoTIFF
                      </span>
                    )}
                  </div>

                  <div className="text-[11px] font-mono text-text-3 flex flex-wrap gap-2 mt-1">
                    <span>{(file.size / (1024 * 1024)).toFixed(1)} MB</span>
                    {meta && (
                      <>
                        <span>•</span>
                        <span>{meta.width || '1920'}x{meta.height || '1080'}</span>
                        <span>•</span>
                        <span>{meta.crs || 'EPSG:32643'}</span>
                        {meta.sensor && (
                          <>
                            <span>•</span>
                            <span className="text-accent">{meta.sensor}</span>
                          </>
                        )}
                      </>
                    )}
                  </div>

                  <div className="text-[11px] text-emerald-400 flex items-center gap-1 mt-0.5">
                    <span>✓</span>
                    <span>Image validated</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => onRemoveFile(idx)}
                  className="text-text-3 hover:text-red-400 p-1 text-xs transition-colors"
                  title="Remove image"
                  aria-label={`Remove ${file.name}`}
                >
                  ✕
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
