import React, { useEffect, useRef, useState } from 'react';
import type { Evidence, OverlayOptions, UploadedFileInfo, ViewMode } from '../../types';
import { ImageLegend } from './ImageLegend';
import { OverlayControls } from './OverlayControls';

interface ImageViewerProps {
  files: UploadedFileInfo[];
  rawFiles?: File[];
  evidence: Evidence[];
  activeEvidenceId?: string | null;
  onClearActiveEvidence?: () => void;
}

export const ImageViewer: React.FC<ImageViewerProps> = ({
  files,
  rawFiles = [],
  evidence,
  activeEvidenceId,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [viewMode, setViewMode] = useState<ViewMode>('single');
  const [splitPos, setSplitPos] = useState(50); // percentage for before/after slider
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hoveredBboxId, setHoveredBboxId] = useState<string | null>(null);

  const [overlays, setOverlays] = useState<OverlayOptions>({
    evidence: true,
    boundingBoxes: true,
    changeHeatmap: true,
    segmentation: false,
  });

  const viewerRef = useRef<HTMLDivElement>(null);

  const hasTwoImages = files.length >= 2;

  useEffect(() => {
    if (hasTwoImages && viewMode === 'single') {
      setViewMode('side-by-side');
    } else if (!hasTwoImages && viewMode !== 'single') {
      setViewMode('single');
    }
  }, [hasTwoImages, viewMode]);

  // Object preview URLs for standard web images
  const getPreviewUrl = (idx: number): string | null => {
    const raw = rawFiles[idx];
    if (!raw) return null;
    const name = raw.name.toLowerCase();
    if (name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.webp')) {
      try {
        return URL.createObjectURL(raw);
      } catch {
        return null;
      }
    }
    return null;
  };

  const preview1 = getPreviewUrl(0);
  const preview2 = getPreviewUrl(1);

  // Zoom controls
  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 4));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.5));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };
  const handleFit = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const toggleFullscreen = () => {
    if (!viewerRef.current) return;
    if (!isFullscreen) {
      if (viewerRef.current.requestFullscreen) {
        viewerRef.current.requestFullscreen();
      }
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
      setIsFullscreen(false);
    }
  };

  // Pan interaction
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  // Filter evidence items
  const bboxItems = evidence.filter((ev) => ev.bbox && Array.isArray(ev.bbox));
  const changeItems = evidence.filter((ev) => ev.evidence_type === 'temporal_difference' && ev.bbox);
  const sensorItems = evidence.filter((ev) => ev.evidence_type === 'sensor_comparison');

  const imgWidth = files[0]?.metadata?.width || 1920;
  const imgHeight = files[0]?.metadata?.height || 1080;

  if (files.length === 0) {
    return (
      <div className="image-viewer-container flex flex-col items-center justify-center p-8 bg-surface rounded-xl border border-glass-border min-h-[420px] text-center">
        <div className="text-5xl mb-3 opacity-30">🛰️</div>
        <div className="text-base font-semibold text-text">No Imagery Loaded</div>
        <div className="text-xs text-text-3 max-w-sm mt-1">
          Upload satellite tiles or choose a demo preset above to activate the high-resolution geospatial viewer canvas.
        </div>
      </div>
    );
  }

  return (
    <div
      ref={viewerRef}
      className={`image-viewer-container relative bg-[#060911] rounded-xl border border-glass-border overflow-hidden flex flex-col ${
        isFullscreen ? 'h-screen w-screen rounded-none' : 'min-h-[480px] h-[520px]'
      }`}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Top Toolbar */}
      <div className="viewer-toolbar flex flex-wrap justify-between items-center px-3 py-2 bg-surface/85 backdrop-blur border-b border-glass-border z-20">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-surface-2 border border-glass-border text-accent font-semibold">
            {hasTwoImages ? `${viewMode.toUpperCase()} VIEW` : 'SINGLE SCENE'}
          </span>

          {hasTwoImages && (
            <div className="flex items-center gap-1 bg-surface-2 p-0.5 rounded border border-glass-border text-xs font-mono">
              <button
                type="button"
                className={`px-2 py-0.5 rounded transition-all cursor-pointer ${
                  viewMode === 'side-by-side' ? 'bg-blue-600 text-white font-bold' : 'text-text-3 hover:text-text'
                }`}
                onClick={() => setViewMode('side-by-side')}
              >
                Side-by-Side
              </button>
              <button
                type="button"
                className={`px-2 py-0.5 rounded transition-all cursor-pointer ${
                  viewMode === 'before-after' ? 'bg-blue-600 text-white font-bold' : 'text-text-3 hover:text-text'
                }`}
                onClick={() => setViewMode('before-after')}
              >
                Split Slider
              </button>
            </div>
          )}

          <span className="text-[10px] font-mono text-text-3 hidden sm:inline">
            Coordinate Space: <strong className="text-text-2">Image Pixels (px)</strong>
          </span>
        </div>

        {/* View Controls: Zoom, Pan, Fit, Fullscreen */}
        <div className="flex items-center gap-1.5 text-xs font-mono">
          <button
            type="button"
            className="px-2 py-1 bg-surface-2 hover:bg-surface-3 rounded border border-glass-border text-text-2 hover:text-text cursor-pointer"
            onClick={handleZoomOut}
            title="Zoom Out"
            aria-label="Zoom Out"
          >
            -
          </button>
          <span className="px-1 text-[11px] text-text-3">{Math.round(zoom * 100)}%</span>
          <button
            type="button"
            className="px-2 py-1 bg-surface-2 hover:bg-surface-3 rounded border border-glass-border text-text-2 hover:text-text cursor-pointer"
            onClick={handleZoomIn}
            title="Zoom In"
            aria-label="Zoom In"
          >
            +
          </button>
          <button
            type="button"
            className="px-2 py-1 bg-surface-2 hover:bg-surface-3 rounded border border-glass-border text-text-2 hover:text-text text-[11px] cursor-pointer"
            onClick={handleReset}
            title="Reset Pan/Zoom"
          >
            Reset
          </button>
          <button
            type="button"
            className="px-2 py-1 bg-surface-2 hover:bg-surface-3 rounded border border-glass-border text-text-2 hover:text-text text-[11px] cursor-pointer"
            onClick={handleFit}
            title="Fit to Screen"
          >
            Fit
          </button>
          <button
            type="button"
            className="px-2 py-1 bg-surface-2 hover:bg-surface-3 rounded border border-glass-border text-text-2 hover:text-text cursor-pointer"
            onClick={toggleFullscreen}
            title="Toggle Fullscreen"
            aria-label="Fullscreen"
          >
            ⛶
          </button>
        </div>
      </div>

      {/* Canvas Viewport Area */}
      <div
        className="canvas-viewport relative flex-1 overflow-hidden cursor-grab active:cursor-grabbing select-none"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
      >
        <div
          className="canvas-transform absolute inset-0 transition-transform duration-75 flex items-center justify-center p-4"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
          }}
        >
          {viewMode === 'before-after' && hasTwoImages ? (
            /* Before/After Split View */
            <div className="relative w-[580px] h-[360px] rounded-lg overflow-hidden border border-glass-border shadow-2xl bg-surface-2">
              {/* Image 1 (T1) */}
              <div className="absolute inset-0 bg-[#0d1b2a] flex flex-col items-center justify-center">
                {preview1 ? (
                  <img src={preview1} alt="T1 Before" className="w-full h-full object-cover" />
                ) : (
                  <>
                    <div className="text-3xl mb-2 opacity-50">🛰️</div>
                    <span className="font-mono text-xs text-text-2 font-bold">T1 (BEFORE)</span>
                    <span className="font-mono text-[10px] text-text-3">{files[0].original_filename}</span>
                  </>
                )}
              </div>

              {/* Image 2 (T2) with Split Clip Path */}
              <div
                className="absolute inset-0 bg-[#1b263b] flex flex-col items-center justify-center border-l-2 border-cyan-400"
                style={{ clipPath: `polygon(${splitPos}% 0, 100% 0, 100% 100%, ${splitPos}% 100%)` }}
              >
                {preview2 ? (
                  <img src={preview2} alt="T2 After" className="w-full h-full object-cover" />
                ) : (
                  <>
                    <div className="text-3xl mb-2 opacity-50">🛰️</div>
                    <span className="font-mono text-xs text-cyan-300 font-bold">T2 (AFTER)</span>
                    <span className="font-mono text-[10px] text-text-3">{files[1].original_filename}</span>
                  </>
                )}
              </div>

              {/* Split Slider Line & Handle */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 cursor-ew-resize z-10"
                style={{ left: `${splitPos}%` }}
                onMouseDown={(e) => e.stopPropagation()}
              >
                <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-cyan-500 text-black font-bold text-[10px] flex items-center justify-center shadow-lg pointer-events-none">
                  ↔
                </div>
              </div>

              <input
                type="range"
                min="0"
                max="100"
                value={splitPos}
                onChange={(e) => setSplitPos(Number(e.target.value))}
                className="absolute bottom-2 left-4 right-4 z-20 opacity-50 hover:opacity-100 transition-opacity"
              />
            </div>
          ) : viewMode === 'side-by-side' && hasTwoImages ? (
            /* Side-by-Side Dual View */
            <div className="grid grid-cols-2 gap-3 w-[720px] max-w-full">
              {/* Slot 1 */}
              <div className="relative h-[340px] rounded-lg border border-glass-border overflow-hidden bg-gradient-to-br from-[#0c1626] to-[#12233f] flex flex-col justify-between p-3 shadow-xl">
                <div className="flex justify-between items-center text-xs font-mono z-10">
                  <span className="px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/40 font-bold">
                    {files[0].metadata?.image_type === 'sar' ? 'SAR SENSOR' : 'OPTICAL (T1)'}
                  </span>
                  <span className="text-text-3 text-[10px]">{files[0].metadata?.acquisition_date || '2024'}</span>
                </div>

                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  {preview1 ? (
                    <img src={preview1} alt="Slot 1" className="w-full h-full object-cover" />
                  ) : (
                    <div className="flex flex-col items-center opacity-70">
                      <div className="text-4xl mb-1">🛰️</div>
                      <span className="font-mono text-[11px] text-text-2 truncate max-w-[200px]">{files[0].original_filename}</span>
                      <span className="font-mono text-[10px] text-text-3">{files[0].metadata?.sensor || 'Sentinel-2'}</span>
                    </div>
                  )}
                </div>

                <div className="text-[10px] font-mono text-text-3 flex justify-between z-10 bg-black/40 px-1 rounded">
                  <span>{files[0].metadata?.crs || 'EPSG:32643'}</span>
                  <span>10m res</span>
                </div>
              </div>

              {/* Slot 2 */}
              <div className="relative h-[340px] rounded-lg border border-glass-border overflow-hidden bg-gradient-to-br from-[#121c2e] to-[#192b47] flex flex-col justify-between p-3 shadow-xl">
                <div className="flex justify-between items-center text-xs font-mono z-10">
                  <span className="px-1.5 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800/40 font-bold">
                    {files[1].metadata?.image_type === 'sar' ? 'SAR SENSOR' : 'OPTICAL (T2)'}
                  </span>
                  <span className="text-text-3 text-[10px]">{files[1].metadata?.acquisition_date || '2025'}</span>
                </div>

                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  {preview2 ? (
                    <img src={preview2} alt="Slot 2" className="w-full h-full object-cover" />
                  ) : (
                    <div className="flex flex-col items-center opacity-70">
                      <div className="text-4xl mb-1">📡</div>
                      <span className="font-mono text-[11px] text-text-2 truncate max-w-[200px]">{files[1].original_filename}</span>
                      <span className="font-mono text-[10px] text-text-3">{files[1].metadata?.sensor || 'Sentinel-1'}</span>
                    </div>
                  )}
                </div>

                <div className="text-[10px] font-mono text-text-3 flex justify-between z-10 bg-black/40 px-1 rounded">
                  <span>{files[1].metadata?.crs || 'EPSG:32643'}</span>
                  <span>10m res</span>
                </div>
              </div>
            </div>
          ) : (
            /* Single Image View Canvas */
            <div className="relative w-[580px] h-[360px] rounded-lg border border-glass-border overflow-hidden bg-gradient-to-br from-[#0a121e] via-[#0f1d32] to-[#142642] flex flex-col justify-between p-4 shadow-2xl">
              <div className="flex justify-between items-center text-xs font-mono z-10">
                <span className="px-2 py-0.5 rounded bg-blue-950/80 text-blue-300 border border-blue-800/40 font-bold">
                  {files[0].metadata?.image_type?.toUpperCase() || 'OPTICAL'}
                </span>
                <span className="text-text-3 text-[11px]">{files[0].original_filename}</span>
              </div>

              {/* Real Image or Raster Simulation Background */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                {preview1 ? (
                  <img src={preview1} alt="Scene" className="w-full h-full object-cover" />
                ) : (
                  <div className="flex flex-col items-center justify-center opacity-40">
                    <div className="text-6xl mb-2">🛰️</div>
                    <div className="font-mono text-xs text-text-3">
                      {files[0].metadata?.sensor || 'Sentinel-2'} Multispectral Tile
                    </div>
                  </div>
                )}
              </div>

              {/* Bounding Box & Evidence Overlays in Image Space Coordinates */}
              {overlays.boundingBoxes &&
                bboxItems.map((ev, idx) => {
                  const [x1, y1, x2, y2] = ev.bbox!;
                  const leftPct = (x1 / imgWidth) * 100;
                  const topPct = (y1 / imgHeight) * 100;
                  const widthPct = ((x2 - x1) / imgWidth) * 100;
                  const heightPct = ((y2 - y1) / imgHeight) * 100;
                  const isActive = activeEvidenceId === ev.evidence_id || hoveredBboxId === ev.evidence_id;

                  return (
                    <div
                      key={ev.evidence_id || idx}
                      className={`absolute rounded transition-all pointer-events-auto cursor-pointer ${
                        isActive
                          ? 'border-2 border-cyan-300 bg-cyan-400/30 ring-4 ring-cyan-500/50'
                          : 'border border-cyan-400/90 bg-cyan-400/15 hover:border-cyan-300'
                      }`}
                      style={{
                        left: `${Math.max(0, leftPct)}%`,
                        top: `${Math.max(0, topPct)}%`,
                        width: `${Math.min(100 - leftPct, widthPct)}%`,
                        height: `${Math.min(100 - topPct, heightPct)}%`,
                      }}
                      onMouseEnter={() => setHoveredBboxId(ev.evidence_id)}
                      onMouseLeave={() => setHoveredBboxId(null)}
                    >
                      <div className="absolute -top-6 left-0 px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 text-[10px] font-mono border border-cyan-700/50 whitespace-nowrap shadow-lg flex items-center gap-1">
                        <span>🎯</span>
                        <span>{ev.claim.substring(0, 20)}...</span>
                        <span className="text-[9px] text-cyan-400 font-bold">({(ev.confidence * 100).toFixed(0)}%)</span>
                      </div>

                      {isActive && (
                        <div className="absolute -bottom-5 left-0 px-1.5 py-0.2 rounded bg-black/80 text-[9px] font-mono text-cyan-200 whitespace-nowrap">
                          Image-Space: [{x1}, {y1}, {x2}, {y2}] px
                        </div>
                      )}
                    </div>
                  );
                })}

              {/* Change Region Highlight Overlays */}
              {overlays.changeHeatmap &&
                changeItems.map((ev, idx) => {
                  const [x1, y1, x2, y2] = ev.bbox!;
                  const leftPct = (x1 / imgWidth) * 100;
                  const topPct = (y1 / imgHeight) * 100;
                  const widthPct = ((x2 - x1) / imgWidth) * 100;
                  const heightPct = ((y2 - y1) / imgHeight) * 100;

                  return (
                    <div
                      key={`chg-${idx}`}
                      className="absolute rounded border border-amber-400 bg-amber-400/20 pointer-events-none"
                      style={{
                        left: `${Math.max(0, leftPct)}%`,
                        top: `${Math.max(0, topPct)}%`,
                        width: `${Math.min(100 - leftPct, widthPct)}%`,
                        height: `${Math.min(100 - topPct, heightPct)}%`,
                      }}
                    >
                      <span className="absolute -top-5 left-0 px-1 py-0.2 rounded bg-amber-950 text-amber-300 text-[9px] font-mono border border-amber-700/50 whitespace-nowrap shadow">
                        Δ Change Detected
                      </span>
                    </div>
                  );
                })}

              <div className="flex justify-between items-center text-[10px] font-mono text-text-3 z-10 bg-black/40 px-2 py-0.5 rounded">
                <span>CRS: {files[0].metadata?.crs || 'EPSG:32643'}</span>
                <span>Bounds: [{imgWidth} × {imgHeight} px]</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Viewer Bar: Legend & Overlay Controls */}
      <div className="viewer-footer flex flex-wrap justify-between items-center px-3 py-2 bg-surface/90 border-t border-glass-border z-20 gap-2">
        <OverlayControls
          overlays={overlays}
          onChange={setOverlays}
          hasBbox={bboxItems.length > 0}
          hasChange={changeItems.length > 0}
        />

        <ImageLegend
          hasBbox={bboxItems.length > 0}
          hasChange={changeItems.length > 0}
          hasSensorComparison={sensorItems.length > 0}
          overlays={overlays}
        />
      </div>
    </div>
  );
};
