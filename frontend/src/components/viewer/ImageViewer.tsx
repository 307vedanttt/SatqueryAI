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
  isAnalyzing?: boolean;
}

export const ImageViewer: React.FC<ImageViewerProps> = ({
  files,
  rawFiles = [],
  evidence,
  activeEvidenceId,
  isAnalyzing = false,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [viewMode, setViewMode] = useState<ViewMode>('single');
  const [splitPos, setSplitPos] = useState(50);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hoveredBboxId, setHoveredBboxId] = useState<string | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);

  const [overlays, setOverlays] = useState<OverlayOptions>({
    evidence: true,
    boundingBoxes: true,
    changeHeatmap: true,
    segmentation: false,
  });

  const viewerRef = useRef<HTMLDivElement>(null);
  const hasTwoImages = files.length >= 2;
  const isLoaded = files.length > 0;

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
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.round(e.clientX - rect.left);
    const y = Math.round(e.clientY - rect.top);
    setMousePos({ x, y });
  };

  const handleMouseUp = () => setIsDragging(false);

  // Evidence filtering
  const bboxItems = evidence.filter((ev) => ev.bbox && Array.isArray(ev.bbox));
  const changeItems = evidence.filter((ev) => ev.evidence_type === 'temporal_difference' && ev.bbox);
  const sensorItems = evidence.filter((ev) => ev.evidence_type === 'sensor_comparison');

  const mainMeta = files[0]?.metadata;
  const imgWidth = mainMeta?.width || 1920;
  const imgHeight = mainMeta?.height || 1080;
  const crsText = mainMeta?.crs || 'EPSG:4326';
  const gsdText = mainMeta?.resolution ? `${mainMeta.resolution[0]}m/PX` : '10m/PX';
  const sensorText = mainMeta?.sensor || (mainMeta?.image_type === 'sar' ? 'Sentinel-1 SAR' : 'Sentinel-2 MSI');

  return (
    <div
      ref={viewerRef}
      className={`imagery-viewer relative bg-[#02050c] rounded-xl border border-white/10 overflow-hidden flex flex-col shadow-2xl shadow-black/60 transition-all ${
        isFullscreen ? 'h-screen w-screen rounded-none' : 'min-h-[480px] h-[500px]'
      }`}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Top Header Command Bar */}
      <div className="flex justify-between items-center px-4 py-2.5 bg-slate-950/80 backdrop-blur-xl border-b border-white/10 z-20">
        <div className="flex items-center gap-2.5">
          <span className={`w-2.5 h-2.5 rounded-full ${
            isAnalyzing
              ? 'bg-cyan-400 shadow-[0_0_10px_#22d3ee] animate-pulse'
              : isLoaded
              ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
              : 'bg-slate-600'
          }`} />
          <h3 className="font-mono text-xs font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <span>GIS INTELLIGENCE WORKSTATION</span>
            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
              isAnalyzing
                ? 'bg-cyan-950/80 text-cyan-300 border-cyan-800/60'
                : isLoaded
                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800/60'
                : 'bg-slate-900 text-slate-400 border-slate-800'
            }`}>
              {isAnalyzing ? '● ANALYZING' : isLoaded ? '● READY' : '● STANDBY'}
            </span>
          </h3>

          {hasTwoImages && isLoaded && !isAnalyzing && (
            <div className="flex items-center gap-1 bg-slate-900/90 p-0.5 rounded-lg border border-white/10 text-[11px] font-mono ml-2">
              <button
                type="button"
                className={`px-2.5 py-0.5 rounded transition-all cursor-pointer ${
                  viewMode === 'side-by-side' ? 'bg-blue-600 text-white font-bold shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
                onClick={() => setViewMode('side-by-side')}
              >
                Side-by-Side
              </button>
              <button
                type="button"
                className={`px-2.5 py-0.5 rounded transition-all cursor-pointer ${
                  viewMode === 'before-after' ? 'bg-blue-600 text-white font-bold shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
                onClick={() => setViewMode('before-after')}
              >
                Split Slider
              </button>
            </div>
          )}
        </div>

        {/* Right Telemetry Information */}
        <div className="flex items-center gap-2.5 text-[11px] font-mono text-slate-400">
          {isLoaded && (
            <>
              <span className="hidden sm:inline-block px-2 py-0.5 rounded bg-slate-900/80 border border-white/5 text-slate-300">
                {sensorText}
              </span>
              <span className="hidden md:inline-block px-2 py-0.5 rounded bg-slate-900/80 border border-white/5 text-slate-300">
                GSD: {gsdText}
              </span>
              <span className="px-2 py-0.5 rounded bg-cyan-950/50 border border-cyan-800/40 text-cyan-300 font-semibold">
                {crsText}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Canvas Viewport Area */}
      <div
        className="canvas-viewport relative flex-1 overflow-hidden cursor-grab active:cursor-grabbing select-none"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
      >
        {/* Fine Reticle Grid Texture Overlay */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(6,182,212,0.03)_0%,transparent_75%)] pointer-events-none z-0" />

        {/* Floating Liquid-Glass Control Cluster (Left) */}
        {isLoaded && (
          <div className="absolute top-3 left-3 z-30 flex flex-col gap-1.5 bg-slate-950/85 backdrop-blur-xl p-1.5 rounded-xl border border-white/10 shadow-2xl shadow-black/80">
            <button
              type="button"
              className="w-7 h-7 flex items-center justify-center text-slate-300 hover:text-white hover:bg-white/10 rounded-lg font-mono text-sm cursor-pointer transition-all"
              onClick={handleZoomIn}
              title="Zoom In (+)"
              aria-label="Zoom In"
            >
              +
            </button>
            <button
              type="button"
              className="w-7 h-7 flex items-center justify-center text-slate-300 hover:text-white hover:bg-white/10 rounded-lg font-mono text-sm cursor-pointer transition-all"
              onClick={handleZoomOut}
              title="Zoom Out (-)"
              aria-label="Zoom Out"
            >
              -
            </button>
            <div className="w-full h-[1px] bg-white/10 my-0.5" />
            <button
              type="button"
              className="w-7 h-7 flex items-center justify-center text-slate-300 hover:text-white hover:bg-white/10 rounded-lg font-mono text-[10px] font-bold cursor-pointer transition-all"
              onClick={handleReset}
              title="Reset Pan & Zoom (1:1)"
            >
              1:1
            </button>
            <button
              type="button"
              className="w-7 h-7 flex items-center justify-center text-slate-300 hover:text-white hover:bg-white/10 rounded-lg font-mono text-xs cursor-pointer transition-all"
              onClick={toggleFullscreen}
              title="Toggle Fullscreen"
              aria-label="Fullscreen"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
              </svg>
            </button>
          </div>
        )}

        {/* Reticle Corner Brackets */}
        <div className="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-cyan-500/60 pointer-events-none z-20" />
        <div className="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-cyan-500/60 pointer-events-none z-20" />
        <div className="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 border-cyan-500/60 pointer-events-none z-20" />
        <div className="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-cyan-500/60 pointer-events-none z-20" />

        {/* --- STATE 1: EMPTY --- */}
        {!isLoaded && !isAnalyzing && (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center z-10">
            <div className="w-16 h-16 rounded-2xl bg-slate-900/90 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-4 shadow-xl shadow-cyan-950/40">
              <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M13 2L3 12" />
                <path d="M7 2L2 7" />
                <path d="M22 17L17 22" />
                <path d="M22 13L13 22" />
                <path d="M8 8l8 8" />
                <circle cx="12" cy="12" r="2" fill="currentColor" className="text-cyan-400" />
                <path d="M19 5a7 7 0 0 1 0 10" />
              </svg>
            </div>
            <h4 className="text-base font-extrabold text-white font-mono uppercase tracking-wide">
              Satellite imagery required
            </h4>
            <p className="text-xs text-slate-400 max-w-sm mt-1.5 leading-relaxed font-sans">
              Upload imagery to begin analysis.
            </p>
          </div>
        )}

        {/* --- STATE 2: ANALYZING --- */}
        {isAnalyzing && (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center z-20 bg-slate-950/85 backdrop-blur-md">
            {/* Radar Scan Sweeper Line Animation */}
            <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/10 via-cyan-400/5 to-transparent animate-pulse pointer-events-none" />

            {/* Processing Radar Loader */}
            <div className="relative w-20 h-20 mb-4 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border-2 border-cyan-500/30 animate-ping" />
              <div className="absolute inset-2 rounded-full border-2 border-cyan-400/60 animate-spin border-t-transparent" />
              <div className="w-10 h-10 rounded-full bg-cyan-950/90 border border-cyan-400 flex items-center justify-center text-cyan-300 shadow-lg shadow-cyan-500/30">
                <svg className="w-5 h-5 animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="9" />
                  <circle cx="12" cy="12" r="3" />
                  <line x1="12" y1="3" x2="12" y2="21" />
                  <line x1="3" y1="12" x2="21" y2="12" />
                </svg>
              </div>
            </div>

            <div className="font-mono text-xs font-bold text-cyan-300 uppercase tracking-widest mb-1 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span>BOUNDED EXECUTION GRAPH RUNNING</span>
            </div>

            <p className="text-xs font-sans text-slate-200 font-semibold mb-2">
              Executing Specialist Tool Pipeline & Synthesizing Multimodal Evidence...
            </p>

            <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-slate-900/90 border border-white/10 text-[11px] font-mono text-slate-400">
              <span className="text-cyan-400">STATUS:</span>
              <span className="text-slate-200 font-semibold">{files[0]?.metadata?.sensor || 'Optical/SAR Specialist'} Active</span>
            </div>
          </div>
        )}

        {/* --- STATE 3: LOADED --- */}
        {isLoaded && (
          <div
            className="canvas-transform absolute inset-0 transition-transform duration-75 flex items-center justify-center p-4"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: 'center center',
            }}
          >
            {viewMode === 'before-after' && hasTwoImages ? (
              /* Split Slider View */
              <div className="relative w-[580px] h-[340px] rounded-xl overflow-hidden border border-white/10 shadow-2xl bg-[#080f1e]">
                {/* Image 1 (T1) */}
                <div className="absolute inset-0 bg-[#070e1c] flex flex-col items-center justify-center">
                  {preview1 ? (
                    <img src={preview1} alt="T1 Baseline" className="w-full h-full object-cover" />
                  ) : (
                    <div className="flex flex-col items-center opacity-60">
                      <span className="font-mono text-xs text-slate-200 font-bold">T1 — BASELINE</span>
                      <span className="font-mono text-[10px] text-slate-400">{files[0].original_filename}</span>
                    </div>
                  )}
                </div>

                {/* Image 2 (T2) with Split Polygon */}
                <div
                  className="absolute inset-0 bg-[#0e1628] flex flex-col items-center justify-center border-l-2 border-cyan-400"
                  style={{ clipPath: `polygon(${splitPos}% 0, 100% 0, 100% 100%, ${splitPos}% 100%)` }}
                >
                  {preview2 ? (
                    <img src={preview2} alt="T2 Target" className="w-full h-full object-cover" />
                  ) : (
                    <div className="flex flex-col items-center opacity-60">
                      <span className="font-mono text-xs text-cyan-300 font-bold">T2 — TARGET</span>
                      <span className="font-mono text-[10px] text-slate-400">{files[1].original_filename}</span>
                    </div>
                  )}
                </div>

                {/* Neon Split Line & Handle */}
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 cursor-ew-resize z-10 shadow-[0_0_10px_#22d3ee]"
                  style={{ left: `${splitPos}%` }}
                  onMouseDown={(e) => e.stopPropagation()}
                >
                  <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-cyan-400 text-slate-950 font-bold text-[10px] flex items-center justify-center shadow-lg pointer-events-none">
                    ↔
                  </div>
                </div>

                <input
                  type="range"
                  min="0"
                  max="100"
                  value={splitPos}
                  onChange={(e) => setSplitPos(Number(e.target.value))}
                  className="absolute bottom-3 left-4 right-4 z-20 opacity-70 hover:opacity-100 transition-opacity cursor-ew-resize"
                />
              </div>
            ) : viewMode === 'side-by-side' && hasTwoImages ? (
              /* Side-by-Side Dual View */
              <div className="grid grid-cols-2 gap-3.5 w-[720px] max-w-full">
                {/* Slot 1 */}
                <div className="relative h-[330px] rounded-xl border border-white/10 overflow-hidden bg-[#080f1e] flex flex-col justify-between p-3.5 shadow-xl">
                  <div className="flex justify-between items-center text-xs font-mono z-10">
                    <span className="px-2 py-0.5 rounded bg-blue-950/80 text-blue-300 border border-blue-800/60 font-bold text-[10px]">
                      {files[0].metadata?.sensor || 'OPTICAL SENSOR'}
                    </span>
                    <span className="text-slate-400 text-[10px]">{files[0].metadata?.acquisition_date || 'T1'}</span>
                  </div>

                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    {preview1 ? (
                      <img src={preview1} alt="Slot 1" className="w-full h-full object-cover" />
                    ) : (
                      <div className="flex flex-col items-center opacity-60">
                        <span className="font-mono text-xs text-slate-200 font-bold truncate max-w-[200px]">{files[0].original_filename}</span>
                      </div>
                    )}
                  </div>

                  <div className="text-[10px] font-mono text-slate-300 flex justify-between z-10 bg-slate-950/80 backdrop-blur-md px-2 py-1 rounded-md border border-white/10">
                    <span>{files[0].metadata?.crs || 'EPSG:4326'}</span>
                    <span>{files[0].metadata?.resolution ? `${files[0].metadata.resolution[0]}m` : '10m GSD'}</span>
                  </div>
                </div>

                {/* Slot 2 */}
                <div className="relative h-[330px] rounded-xl border border-white/10 overflow-hidden bg-[#080f1e] flex flex-col justify-between p-3.5 shadow-xl">
                  <div className="flex justify-between items-center text-xs font-mono z-10">
                    <span className="px-2 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-800/60 font-bold text-[10px]">
                      {files[1].metadata?.sensor || 'SAR SENSOR'}
                    </span>
                    <span className="text-slate-400 text-[10px]">{files[1].metadata?.acquisition_date || 'T2'}</span>
                  </div>

                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    {preview2 ? (
                      <img src={preview2} alt="Slot 2" className="w-full h-full object-cover" />
                    ) : (
                      <div className="flex flex-col items-center opacity-60">
                        <span className="font-mono text-xs text-slate-200 font-bold truncate max-w-[200px]">{files[1].original_filename}</span>
                      </div>
                    )}
                  </div>

                  <div className="text-[10px] font-mono text-slate-300 flex justify-between z-10 bg-slate-950/80 backdrop-blur-md px-2 py-1 rounded-md border border-white/10">
                    <span>{files[1].metadata?.crs || 'EPSG:4326'}</span>
                    <span>{files[1].metadata?.resolution ? `${files[1].metadata.resolution[0]}m` : '10m GSD'}</span>
                  </div>
                </div>
              </div>
            ) : (
              /* Single Scene View Canvas */
              <div className="relative w-[580px] h-[340px] rounded-xl border border-white/10 overflow-hidden bg-[#080f1e] flex flex-col justify-between p-4 shadow-2xl">
                <div className="flex justify-between items-center text-xs font-mono z-10">
                  <span className="px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 font-bold text-[10px]">
                    {files[0].metadata?.image_type?.toUpperCase() || 'SATELLITE RASTER'}
                  </span>
                  <span className="text-slate-400 text-[11px] font-mono truncate max-w-[260px]">{files[0].original_filename}</span>
                </div>

                {/* Actual Uploaded Image Canvas */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  {preview1 ? (
                    <img src={preview1} alt="Scene" className="w-full h-full object-cover" />
                  ) : (
                    <div className="flex flex-col items-center justify-center opacity-40">
                      <div className="font-mono text-xs text-slate-300 font-bold">
                        {files[0].metadata?.sensor || 'Sentinel-2'} Raster Tile
                      </div>
                    </div>
                  )}
                </div>

                {/* Bounding Box & Evidence Overlays in Image Space */}
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
                            ? 'border-2 border-cyan-300 bg-cyan-400/25 ring-4 ring-cyan-500/40 shadow-[0_0_16px_rgba(6,182,212,0.4)]'
                            : 'border border-cyan-400/90 bg-cyan-400/10 hover:border-cyan-300'
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
                        <div className="absolute -top-6 left-0 px-2 py-0.5 rounded-md bg-[#071326] text-cyan-300 text-[10px] font-mono border border-cyan-700/60 whitespace-nowrap shadow-lg flex items-center gap-1.5">
                          <span>🎯</span>
                          <span>{ev.claim.substring(0, 20)}...</span>
                          <span className="text-[9px] text-cyan-400 font-bold">({(ev.confidence * 100).toFixed(0)}%)</span>
                        </div>

                        {isActive && (
                          <div className="absolute -bottom-5 left-0 px-2 py-0.5 rounded bg-black/85 text-[9px] font-mono text-cyan-200 whitespace-nowrap border border-slate-700">
                            BBox: [{x1}, {y1}, {x2}, {y2}] px
                          </div>
                        )}
                      </div>
                    );
                  })}

                {/* Change Region Highlights */}
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
                        <span className="absolute -top-5 left-0 px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 text-[9px] font-mono border border-amber-700/60 whitespace-nowrap shadow">
                          Δ Change Region
                        </span>
                      </div>
                    );
                  })}

                <div className="flex justify-between items-center text-[10px] font-mono text-slate-300 z-10 bg-slate-950/80 backdrop-blur-md px-2 py-1 rounded-md border border-white/10">
                  <span>CRS: {crsText}</span>
                  <span>Dimensions: [{imgWidth} × {imgHeight} px]</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Bottom Coordinates & Scale Bar */}
        <div className="absolute bottom-2 left-4 right-4 z-20 flex justify-between items-center text-[10px] font-mono text-slate-400 pointer-events-none">
          <div className="flex items-center gap-1.5 bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded-md border border-white/10 pointer-events-auto">
            <span className="w-6 h-[2px] bg-cyan-400 inline-block" />
            <span>500 m</span>
          </div>

          <div className="bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded-md border border-white/10 pointer-events-auto flex items-center gap-2">
            <span>{mousePos ? `x: ${mousePos.x}px, y: ${mousePos.y}px` : '12.9716°N, 77.5946°E'}</span>
            <span>•</span>
            <span className="text-cyan-400 font-bold">{Math.round(zoom * 100)}%</span>
          </div>
        </div>
      </div>

      {/* Bottom Toolbar: Overlay Controls & Legend */}
      <div className="flex flex-wrap justify-between items-center px-4 py-2 bg-slate-950/80 border-t border-white/10 z-20 gap-2">
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
