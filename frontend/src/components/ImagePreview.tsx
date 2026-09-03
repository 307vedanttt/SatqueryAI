import React from 'react';
import type { UploadedFileInfo } from '../types';

interface ImagePreviewProps {
  files: UploadedFileInfo[];
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({ files }) => {
  if (!files || files.length === 0) return null;

  return (
    <div className="card mt-3">
      <div className="card-title">
        <span className="icon">🖼️</span>
        <span>Input Imagery & Metadata</span>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {files.map((file) => (
          <div key={file.file_id} className="p-2 border border-glass-border rounded-md bg-surface">
            <div className="font-semibold text-xs truncate mb-1">{file.original_filename}</div>
            <div className="text-xs text-text-3 font-mono flex flex-col gap-1">
              <div>Size: {(file.size_bytes / (1024 * 1024)).toFixed(2)} MB</div>
              <div>GeoTIFF: {file.is_geotiff ? 'Yes' : 'No'}</div>
              {file.metadata && (
                <>
                  <div>Dimensions: {file.metadata.width} x {file.metadata.height}</div>
                  <div>CRS: {file.metadata.crs || 'Unspecified'}</div>
                  {file.metadata.sensor && <div>Sensor: {file.metadata.sensor}</div>}
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
