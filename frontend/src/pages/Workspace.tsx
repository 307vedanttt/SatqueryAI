import React, { useState } from 'react';
import type {
  AnalysisResponse,
  InputConfiguration,
  UploadedFileInfo,
} from '../types';
import { ModeAwareUploader, type AnalysisMode } from '../components/upload/ModeAwareUploader';
import { ImageViewer } from '../components/viewer/ImageViewer';
import { QuerySection } from '../components/analysis/QuerySection';
import { AnalysisProgress } from '../components/analysis/AnalysisProgress';
import { ResponsePanel } from '../components/analysis/ResponsePanel';
import { EvidencePanel } from '../components/evidence/EvidencePanel';
import { ExecutionTrace } from '../components/trace/ExecutionTrace';
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
    // Clear previous results when intentionally switching workflow modes
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

  // Quick Demo Presets
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
      setQuery('Where are the buildings?');
      handleFilesSelected([f]);
    } else if (presetType === 'optical-sar') {
      setMode('optical-sar');
      const f1 = new File([''], 'sentinel2_optical.tif', { type: 'image/tiff' });
      const f2 = new File([''], 'sentinel1_sar_vv.tif', { type: 'image/tiff' });
      setFiles([f1, f2]);
      setQuery('What complementary information do these images provide?');
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
      const msg = err instanceof Error ? err.message : 'Analysis reasoning pipeline failed.';
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
    <div className="workspace-page flex flex-col gap-5">
      {/* Top Demo Quick-Bar */}
      <div className="demo-bar flex flex-wrap items-center justify-between gap-2.5 p-2.5 rounded-xl bg-[#0c1322] border border-slate-800/80 shadow-sm">
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <span className="text-cyan-400">⚡</span>
          <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">
            QUICK SCENARIOS:
          </span>
          <button
            type="button"
            className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-700/80 border border-slate-700/50 text-slate-300 hover:text-white transition-all cursor-pointer text-[11px] font-semibold"
            onClick={() => handleLoadDemoPreset('vqa')}
          >
            1. Single VQA
          </button>
          <button
            type="button"
            className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-700/80 border border-slate-700/50 text-slate-300 hover:text-white transition-all cursor-pointer text-[11px] font-semibold"
            onClick={() => handleLoadDemoPreset('grounding')}
          >
            2. Grounding
          </button>
          <button
            type="button"
            className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-700/80 border border-slate-700/50 text-slate-300 hover:text-white transition-all cursor-pointer text-[11px] font-semibold"
            onClick={() => handleLoadDemoPreset('optical-sar')}
          >
            3. Optical + SAR
          </button>
          <button
            type="button"
            className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-700/80 border border-slate-700/50 text-slate-300 hover:text-white transition-all cursor-pointer text-[11px] font-semibold"
            onClick={() => handleLoadDemoPreset('change')}
          >
            4. Bi-Temporal Change
          </button>
        </div>

        <div className="text-[11px] font-mono text-slate-500 hidden md:block">
          Select scenario or drag imagery below to initiate analysis.
        </div>
      </div>

      {/* Main Two-Column Analysis Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Column: IMAGE WORKSPACE (Col 1 to 7) */}
        <div className="lg:col-span-7 flex flex-col gap-4">
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

          <ImageViewer
            files={uploadedInfos}
            rawFiles={files}
            evidence={analysisResult?.evidence || []}
            activeEvidenceId={activeEvidenceId}
            onClearActiveEvidence={() => setActiveEvidenceId(null)}
          />
        </div>

        {/* Right Column: AI ANALYSIS & REASONING PANEL (Col 8 to 12) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <QuerySection
            query={query}
            onQueryChange={setQuery}
            onSubmit={handleRunAnalysis}
            onClear={() => setQuery('')}
            isAnalyzing={isAnalyzing}
            canAnalyze={uploadedInfos.length > 0 && query.trim().length > 0 && !isUploading}
            configuration={detectedConfig}
          />

          <AnalysisProgress isAnalyzing={isAnalyzing} />

          <ResponsePanel
            result={analysisResult}
            isLoading={isAnalyzing}
          />

          {/* Supporting Evidence categorized directly below the response */}
          {analysisResult && (
            <EvidencePanel
              evidence={analysisResult.evidence || []}
              activeEvidenceId={activeEvidenceId}
              onFocusEvidence={(id) => setActiveEvidenceId(id)}
            />
          )}
        </div>
      </div>

      {/* Bottom Section: EXECUTION TRACE (Full Width) */}
      {analysisResult?.execution_trace && analysisResult.execution_trace.length > 0 && (
        <div className="w-full mt-2">
          <ExecutionTrace steps={analysisResult.execution_trace} />
        </div>
      )}
    </div>
  );
};
