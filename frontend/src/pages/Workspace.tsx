import React, { useState } from 'react';
import type {
  AnalysisResponse,
  InputConfiguration,
  UploadedFileInfo,
} from '../types';
import { UploadZone } from '../components/upload/UploadZone';
import { ValidationPanel } from '../components/upload/ValidationPanel';
import { ConfigurationCard } from '../components/upload/ConfigurationCard';
import { MetadataCard } from '../components/metadata/MetadataCard';
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
  const [files, setFiles] = useState<File[]>([]);
  const [uploadedInfos, setUploadedInfos] = useState<UploadedFileInfo[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [uploadId, setUploadId] = useState<string | null>(null);

  const [query, setQuery] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [selectedMetaIndex, setSelectedMetaIndex] = useState(0);
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null);

  // Handle file uploads
  const handleFilesSelected = async (newFiles: File[]) => {
    // Limit to at most 2 files
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

  // Demo presets for quick testing of all 4 scenarios
  const handleLoadDemoPreset = (type: 'vqa' | 'grounding' | 'optical-sar' | 'change') => {
    setError(null);
    setAnalysisResult(null);

    if (type === 'vqa') {
      const f = new File([''], 'sentinel2_optical_scene.tif', { type: 'image/tiff' });
      setFiles([f]);
      setQuery('What is visible in this image?');
      handleFilesSelected([f]);
    } else if (type === 'grounding') {
      const f = new File([''], 'bangalore_urban_area.tif', { type: 'image/tiff' });
      setFiles([f]);
      setQuery('Where are the buildings?');
      handleFilesSelected([f]);
    } else if (type === 'optical-sar') {
      const f1 = new File([''], 'sentinel2_optical.tif', { type: 'image/tiff' });
      const f2 = new File([''], 'sentinel1_sar_vv.tif', { type: 'image/tiff' });
      setFiles([f1, f2]);
      setQuery('What complementary information do these images provide?');
      handleFilesSelected([f1, f2]);
    } else if (type === 'change') {
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
      {/* Workflow Quick-Launch Banner */}
      <div className="demo-bar flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-xl bg-surface/80 border border-glass-border">
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-accent">🚀</span>
          <span className="text-text-2 font-bold uppercase tracking-wider text-[10px]">
            DEMO PRESETS:
          </span>
          <button
            type="button"
            className="px-2 py-0.5 rounded bg-surface-2 hover:bg-blue-900/40 border border-glass-border text-text-2 hover:text-white transition-colors"
            onClick={() => handleLoadDemoPreset('vqa')}
          >
            1. Single VQA
          </button>
          <button
            type="button"
            className="px-2 py-0.5 rounded bg-surface-2 hover:bg-cyan-900/40 border border-glass-border text-text-2 hover:text-white transition-colors"
            onClick={() => handleLoadDemoPreset('grounding')}
          >
            2. Grounding
          </button>
          <button
            type="button"
            className="px-2 py-0.5 rounded bg-surface-2 hover:bg-purple-900/40 border border-glass-border text-text-2 hover:text-white transition-colors"
            onClick={() => handleLoadDemoPreset('optical-sar')}
          >
            3. Optical + SAR
          </button>
          <button
            type="button"
            className="px-2 py-0.5 rounded bg-surface-2 hover:bg-emerald-900/40 border border-glass-border text-text-2 hover:text-white transition-colors"
            onClick={() => handleLoadDemoPreset('change')}
          >
            4. Bi-Temporal Change
          </button>
        </div>

        <div className="text-[11px] font-mono text-text-3 hidden lg:block">
          Click any preset to auto-load sample satellite tiles and queries.
        </div>
      </div>

      {/* Main 3-Column Analysis Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Column 1: INPUT (Col 1-3) */}
        <div className="lg:col-span-3 flex flex-col gap-4">
          <UploadZone
            files={files}
            uploadedInfos={uploadedInfos}
            onFilesSelected={handleFilesSelected}
            onRemoveFile={handleRemoveFile}
            isUploading={isUploading}
            error={error}
          />

          <ConfigurationCard
            files={uploadedInfos}
            configuration={detectedConfig}
          />

          <ValidationPanel
            files={uploadedInfos}
            isUploading={isUploading}
          />

          <MetadataCard
            files={uploadedInfos}
            selectedFileIndex={selectedMetaIndex}
            onSelectFileIndex={setSelectedMetaIndex}
          />
        </div>

        {/* Column 2: SATELLITE IMAGE VIEWER (Col 4-8) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <ImageViewer
            files={uploadedInfos}
            evidence={analysisResult?.evidence || []}
            activeEvidenceId={activeEvidenceId}
            onClearActiveEvidence={() => setActiveEvidenceId(null)}
          />
        </div>

        {/* Column 3: AI REASONING & ANALYSIS (Col 9-12) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <QuerySection
            query={query}
            onQueryChange={setQuery}
            onSubmit={handleRunAnalysis}
            isAnalyzing={isAnalyzing}
            canAnalyze={uploadedInfos.length > 0 && query.trim().length > 0 && !isUploading}
            configuration={detectedConfig}
          />

          <AnalysisProgress isAnalyzing={isAnalyzing} />

          <ResponsePanel
            result={analysisResult}
            isLoading={isAnalyzing}
          />
        </div>
      </div>

      {/* Bottom Section 1: EVIDENCE */}
      <div className="w-full">
        <EvidencePanel
          evidence={analysisResult?.evidence || []}
          activeEvidenceId={activeEvidenceId}
          onFocusEvidence={(id) => setActiveEvidenceId(id)}
        />
      </div>

      {/* Bottom Section 2: EXECUTION TRACE */}
      {analysisResult?.execution_trace && analysisResult.execution_trace.length > 0 && (
        <div className="w-full">
          <ExecutionTrace steps={analysisResult.execution_trace} />
        </div>
      )}
    </div>
  );
};
