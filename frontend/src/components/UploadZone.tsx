import React, { useRef, useState } from 'react';
import type { UploadedFileInfo } from '../types';

interface UploadZoneProps {
  files: File[];
  uploadedInfos: UploadedFileInfo[];
  onFilesSelected: (files: File[]) => void;
  onRemoveFile: (index: number) => void;
  isUploading: boolean;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  files,
  uploadedInfos,
  onFilesSelected,
  onRemoveFile,
  isUploading,
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

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelected(Array.from(e.target.files));
    }
  };

  return (
    <div>
      <div
        className={`upload-zone ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".tif,.tiff,.png,.jpg,.jpeg"
          onChange={handleFileChange}
        />
        <div className="upload-icon">🛰️</div>
        <div className="upload-zone-title">
          {isUploading ? 'Uploading & Analyzing Metadata...' : 'Drop Remote Sensing Imagery Here'}
        </div>
        <div className="upload-zone-sub">
          Supports GeoTIFF (.tif, .tiff), PNG, JPG (Single, Pair, or Bi-temporal)
        </div>
      </div>

      {files.length > 0 && (
        <div className="upload-previews mt-2">
          {files.map((file, idx) => {
            const isGeoTIFF = file.name.toLowerCase().endsWith('.tif') || file.name.toLowerCase().endsWith('.tiff');
            const previewUrl = isGeoTIFF ? null : URL.createObjectURL(file);

            return (
              <div key={`${file.name}-${idx}`} className="preview-thumb">
                {previewUrl ? (
                  <img src={previewUrl} alt={file.name} />
                ) : (
                  <div className="flex items-center justify-center h-full text-xs font-mono text-center p-1 bg-surface-2">
                    GEOTIFF
                  </div>
                )}
                {isGeoTIFF && <span className="geo-badge">GEO</span>}
                <button
                  type="button"
                  className="remove-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveFile(idx);
                  }}
                  title="Remove file"
                >
                  ✕
                </button>
              </div>
            );
          })}
        </div>
      )}

      {uploadedInfos.length > 0 && (
        <div className="flex flex-col gap-1 mt-2">
          {uploadedInfos.map((info) => (
            <div key={info.file_id} className="file-info flex justify-between items-center">
              <span>📄 {info.original_filename}</span>
              {info.metadata && (
                <span className="font-mono text-xs text-text-3">
                  {info.metadata.width}x{info.metadata.height} | {info.metadata.crs || 'No CRS'}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
