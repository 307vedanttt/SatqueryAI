import React, { useEffect, useState } from 'react';
import { UploadZone } from './components/UploadZone';
import { QueryInput } from './components/QueryInput';
import { AnalyzeButton } from './components/AnalyzeButton';
import { ResultPanel } from './components/ResultPanel';
import { ImagePreview } from './components/ImagePreview';
import { getHealth, uploadFiles, runAnalysis } from './services/api';
import type { AnalysisResponse, HealthResponse, UploadedFileInfo } from './types';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadedInfos, setUploadedInfos] = useState<UploadedFileInfo[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [query, setQuery] = useState('');

  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err) => console.warn('Health check failed:', err));
  }, []);

  const handleFilesSelected = async (files: File[]) => {
    setSelectedFiles(files);
    setError(null);
    setIsUploading(true);

    try {
      const resp = await uploadFiles(files, sessionId);
      setSessionId(resp.session_id);
      setUploadId(resp.upload_id);
      setUploadedInfos(resp.files);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'File upload failed.';
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemoveFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    const newInfos = uploadedInfos.filter((_, i) => i !== index);
    setSelectedFiles(newFiles);
    setUploadedInfos(newInfos);
    if (newFiles.length === 0) {
      setUploadId(null);
    }
  };

  const handleRunAnalysis = async () => {
    if (!sessionId || !uploadId || uploadedInfos.length === 0 || !query.trim()) return;

    setIsAnalyzing(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const resp = await runAnalysis({
        session_id: sessionId,
        upload_id: uploadId,
        file_ids: uploadedInfos.map((i) => i.file_id),
        query: query.trim(),
      });
      setAnalysisResult(resp);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Analysis failed.';
      setError(msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const canAnalyze = uploadedInfos.length > 0 && query.trim().length > 0 && !isUploading;

  return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">🛰️</div>
          <div>
            <div className="header-title">SATQUERY AI</div>
            <div className="header-subtitle">Interactive Remote Sensing Assistant</div>
          </div>
        </div>

        <div className="header-badge">
          <span className="badge badge-isro">ISRO SIH 26167</span>
          {health?.demo_mode && <span className="badge badge-demo">DEMO MODE</span>}
          <div className="flex items-center gap-1 text-xs text-text-3 ml-2">
            <span className={`status-dot ${health?.status === 'ok' ? 'ok' : 'degraded'}`} />
            <span>{health ? health.status.toUpperCase() : 'CONNECTING'}</span>
          </div>
        </div>
      </header>

      <main className="main-grid">
        <div className="flex flex-col gap-3">
          <div className="card">
            <div className="card-title">
              <span className="icon">📥</span>
              <span>1. Upload Imagery</span>
            </div>
            <UploadZone
              files={selectedFiles}
              uploadedInfos={uploadedInfos}
              onFilesSelected={handleFilesSelected}
              onRemoveFile={handleRemoveFile}
              isUploading={isUploading}
            />
          </div>

          <div className="card">
            <div className="card-title">
              <span className="icon">💡</span>
              <span>2. Natural Language Query</span>
            </div>
            <QueryInput value={query} onChange={setQuery} disabled={isAnalyzing} />
            <AnalyzeButton
              onClick={handleRunAnalysis}
              isLoading={isAnalyzing}
              disabled={!canAnalyze}
            />
          </div>

          <ImagePreview files={uploadedInfos} />
        </div>

        <div>
          <ResultPanel result={analysisResult} isLoading={isAnalyzing} error={error} />
        </div>
      </main>

      <footer className="footer">
        <div>SatQuery AI v0.1.0 — SIH 2026 / ISRO Department of Space</div>
        <div>"Don't choose the model. Ask the question."</div>
      </footer>
    </div>
  );
};
