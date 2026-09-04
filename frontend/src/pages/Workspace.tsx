import React, { useState } from 'react';
import type {
  AnalysisResponse,
  InputConfiguration,
  UploadedFileInfo,
} from '../types';
import { WorkflowSidebar } from '../components/layout/WorkflowSidebar';
import { ModeAwareUploader, type AnalysisMode } from '../components/upload/ModeAwareUploader';
import { ImageViewer } from '../components/viewer/ImageViewer';
import { QuerySection } from '../components/analysis/QuerySection';
import { AnalysisProgress } from '../components/analysis/AnalysisProgress';
import { EvidenceAndResultsPanel } from '../components/analysis/EvidenceAndResultsPanel';
import { runAnalysis, uploadFiles } from '../services/api';

interface WorkspaceProps {
  onRecordHistory?: (result: AnalysisResponse, query: string) => void;
}

export const Workspace: React.FC<WorkspaceProps> = ({ onRecordHistory }) => {
  const [mode, setMode] = useState<AnalysisMode>('single');
  const [files, setFiles] = useState<File[]>([]);
  const [uploadedInfos, setUploadedInfos] = useState<UploadedFileInfo[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [uploadId, setUploadId] = useState<string | null>(null);

  const [query, setQuery] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null);

  // Switch analysis modes
  const handleModeChange = (newMode: AnalysisMode) => {
    setMode(newMode);
    setAnalysisResult(null);
    setError(null);
  };

  // Upload handling
  const handleFilesSelected = async (newFiles: File[]) => {
    const combinedFiles = [...files, ...newFiles].slice(0, 2);
    setFiles(combinedFiles);
    setError(null);
    setIsUploading(true);

    try {
      const resp = await uploadFiles(combinedFiles, sessionId);
      setSessionId(resp.session_id);
      setUploadId(resp.upload_id);
      setUploadedInfos(resp.files);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Imagery upload failed.';
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleReplaceFile = async (slotIndex: number, newFile: File) => {
    const updatedFiles = [...files];
    updatedFiles[slotIndex] = newFile;
    setFiles(updatedFiles);
    setError(null);
    setIsUploading(true);

    try {
      const resp = await uploadFiles(updatedFiles, sessionId);
      setSessionId(resp.session_id);
      setUploadId(resp.upload_id);
      setUploadedInfos(resp.files);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'File update failed.';
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemoveFile = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index);
    const updatedInfos = uploadedInfos.filter((_, i) => i !== index);
    setFiles(updatedFiles);
    setUploadedInfos(updatedInfos);
    if (updatedFiles.length === 0) {
      setUploadId(null);
      setAnalysisResult(null);
    }
  };

  const handleClearAll = () => {
    setFiles([]);
    setUploadedInfos([]);
    setUploadId(null);
    setAnalysisResult(null);
    setQuery('');
    setError(null);
    setActiveEvidenceId(null);
  };

  // Quick Demo Scenarios
  const handleLoadDemoPreset = (presetType: 'vqa' | 'grounding' | 'optical-sar' | 'change') => {
    setError(null);
    setAnalysisResult(null);

    if (presetType === 'vqa') {
      setMode('single');
      const f = new File([''], 'sentinel2_optical_scene.tif', { type: 'image/tiff' });
      setFiles([f]);
      setQuery('What is visible in this image?');
      handleFilesSelected([f]);
    } else if (presetType === 'grounding') {
      setMode('single');
      const f = new File([''], 'bangalore_urban_area.tif', { type: 'image/tiff' });
      setFiles([f]);
      setQuery('Where are the major buildings?');
      handleFilesSelected([f]);
    } else if (presetType === 'optical-sar') {
      setMode('optical-sar');
      const f1 = new File([''], 'sentinel2_optical.tif', { type: 'image/tiff' });
      const f2 = new File([''], 'sentinel1_sar_vv.tif', { type: 'image/tiff' });
      setFiles([f1, f2]);
      setQuery('What complementary information do these sensors provide?');
      handleFilesSelected([f1, f2]);
    } else if (presetType === 'change') {
      setMode('bi-temporal');
      const f1 = new File([''], 'sentinel_t1_2024.tif', { type: 'image/tiff' });
      const f2 = new File([''], 'sentinel_t2_2025.tif', { type: 'image/tiff' });
      setFiles([f1, f2]);
      setQuery('What changed between these images?');
      handleFilesSelected([f1, f2]);
    }
  };

  // Run analysis pipeline
  const handleRunAnalysis = async () => {
    if (!query.trim() || uploadedInfos.length === 0) return;

    setIsAnalyzing(true);
    setError(null);
    setActiveEvidenceId(null);

    try {
      const resp = await runAnalysis(
        {
          session_id: sessionId || 'demo-session',
          upload_id: uploadId || 'demo-upload',
          file_ids: uploadedInfos.map((f) => f.file_id),
          query: query.trim(),
        },
        uploadedInfos
      );

      setAnalysisResult(resp);
      if (onRecordHistory) {
        onRecordHistory(resp, query.trim());
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Specialist analysis could not be completed.';
      setError(msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const detectedConfig: InputConfiguration | undefined =
    analysisResult?.input?.configuration ||
    (uploadedInfos.length === 1
      ? uploadedInfos[0].metadata?.image_type === 'sar'
        ? 'SINGLE_SAR'
        : 'SINGLE_OPTICAL'
      : uploadedInfos.length === 2
      ? uploadedInfos[0].metadata?.image_type !== uploadedInfos[1].metadata?.image_type
        ? 'OPTICAL_SAR_PAIR'
        : 'BI_TEMPORAL'
      : undefined);

  return (
    <div className="workspace-page flex flex-col gap-4">
      {/* Quick Demo Presets Bar */}
      <div className="demo-bar flex flex-wrap items-center justify-between gap-2.5 p-2 rounded-xl bg-slate-950/70 backdrop-blur-md border border-white/10 shadow-sm">
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <span className="text-cyan-400 font-bold text-xs pl-1 flex items-center gap-1">
            <span>⚡</span> DEMO PRESETS:
          </span>
          <button
            type="button"
            className="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-white/10 text-slate-300 hover:text-white transition-all cursor-pointer text-[11px] font-semibold"
            onClick={() => handleLoadDemoPreset('vqa')}
          >
            1. Single Scene
          </button>
          <button
            type="button"
            className="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-white/10 text-slate-300 hover:text-white transition-all cursor-pointer text-[11px] font-semibold"
            onClick={() => handleLoadDemoPreset('grounding')}
          >
            2. Grounding
          </button>
          <button
            type="button"
            className="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-white/10 text-slate-300 hover:text-white transition-all cursor-pointer text-[11px] font-semibold"
            onClick={() => handleLoadDemoPreset('optical-sar')}
          >
            3. Optical + SAR
          </button>
          <button
            type="button"
            className="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-white/10 text-slate-300 hover:text-white transition-all cursor-pointer text-[11px] font-semibold"
            onClick={() => handleLoadDemoPreset('change')}
          >
            4. Bi-Temporal Change
          </button>
        </div>
      </div>

      {/* Mobile / Tablet Horizontal Workflow Stepper (visible on < lg screens) */}
      <div className="lg:hidden flex items-center justify-between p-2.5 rounded-xl bg-[#0a101d] border border-slate-800 text-[10.5px] font-mono text-slate-400 overflow-x-auto gap-2">
        <div className="flex items-center gap-1 shrink-0">
          <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold ${
            files.length > 0 ? 'bg-emerald-950 text-emerald-400 border border-emerald-600/60' : 'bg-blue-600 text-white'
          }`}>
            {files.length > 0 ? '✓' : '1'}
          </span>
          <span className={files.length === 0 ? 'text-white font-semibold' : 'text-slate-300'}>Upload</span>
        </div>
        <span className="text-slate-700 shrink-0">→</span>

        <div className="flex items-center gap-1 shrink-0">
          <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold ${
            files.length > 0 ? 'bg-emerald-950 text-emerald-400 border border-emerald-600/60' : 'bg-slate-900 text-slate-500'
          }`}>
            {files.length > 0 ? '✓' : '2'}
          </span>
          <span className="text-slate-300">Config</span>
        </div>
        <span className="text-slate-700 shrink-0">→</span>

        <div className="flex items-center gap-1 shrink-0">
          <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold ${
            query.trim() ? 'bg-emerald-950 text-emerald-400 border border-emerald-600/60' : files.length > 0 ? 'bg-blue-600 text-white' : 'bg-slate-900 text-slate-500'
          }`}>
            {query.trim() ? '✓' : '3'}
          </span>
          <span className={files.length > 0 && !query.trim() ? 'text-white font-semibold' : 'text-slate-300'}>Query</span>
        </div>
        <span className="text-slate-700 shrink-0">→</span>

        <div className="flex items-center gap-1 shrink-0">
          <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold ${
            analysisResult ? 'bg-emerald-950 text-emerald-400 border border-emerald-600/60' : isAnalyzing ? 'bg-blue-600 text-white animate-pulse' : 'bg-slate-900 text-slate-500'
          }`}>
            {analysisResult ? '✓' : '4'}
          </span>
          <span className={isAnalyzing ? 'text-cyan-300 font-semibold' : 'text-slate-300'}>Run</span>
        </div>
        <span className="text-slate-700 shrink-0">→</span>

        <div className="flex items-center gap-1 shrink-0">
          <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold ${
            analysisResult ? 'bg-emerald-950 text-emerald-400 border border-emerald-600/60' : 'bg-slate-900 text-slate-500'
          }`}>
            {analysisResult ? '✓' : '5'}
          </span>
          <span className={analysisResult ? 'text-emerald-300 font-semibold' : 'text-slate-500'}>Result</span>
        </div>
      </div>

      {/* Main 3-Column Workspace */}
      <div className="workspace-3col grid grid-cols-1 lg:grid-cols-[240px_1fr_390px] gap-4 items-start">
        {/* Column 1: Left Workflow Sidebar (240px) */}
        <div className="hidden lg:block">
          <WorkflowSidebar
            hasFiles={files.length > 0}
            hasQuery={Boolean(query.trim())}
            isAnalyzing={isAnalyzing}
            result={analysisResult}
            error={error}
          />
        </div>

        {/* Column 2: Center Main Analysis Workspace */}
        <div className="flex flex-col gap-4 min-w-0">
          {/* Imagery Viewer */}
          <ImageViewer
            files={uploadedInfos}
            rawFiles={files}
            evidence={analysisResult?.evidence || []}
            activeEvidenceId={activeEvidenceId}
            onClearActiveEvidence={() => setActiveEvidenceId(null)}
            isAnalyzing={isAnalyzing}
          />

          {/* Configuration & Ingestion */}
          <ModeAwareUploader
            mode={mode}
            onModeChange={handleModeChange}
            files={files}
            uploadedInfos={uploadedInfos}
            onFilesSelected={handleFilesSelected}
            onReplaceFile={handleReplaceFile}
            onRemoveFile={handleRemoveFile}
            onClearAll={handleClearAll}
            isUploading={isUploading}
            error={error}
            detectedConfiguration={detectedConfig}
          />

          {/* Ask Question & Analyze */}
          <QuerySection
            query={query}
            onQueryChange={setQuery}
            onSubmit={handleRunAnalysis}
            onClear={() => setQuery('')}
            isAnalyzing={isAnalyzing}
            canAnalyze={uploadedInfos.length > 0 && query.trim().length > 0 && !isUploading}
            hasResult={Boolean(analysisResult)}
            configuration={detectedConfig}
            error={error}
          />

          {/* Analysis Progress indicator during execution */}
          <AnalysisProgress
            isAnalyzing={isAnalyzing}
            result={analysisResult}
            error={error}
          />
        </div>

        {/* Column 3: Right Evidence & AI Results Panel (390px) */}
        <div className="w-full">
          <EvidenceAndResultsPanel
            result={analysisResult}
            isLoading={isAnalyzing}
            activeEvidenceId={activeEvidenceId}
            onFocusEvidence={(id) => setActiveEvidenceId(id)}
            onClearTrace={() => setAnalysisResult(null)}
          />
        </div>
      </div>
    </div>
  );
};
