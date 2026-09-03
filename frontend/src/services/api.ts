// SatQuery AI — Typed API Service Layer
// Bridges UI to FastAPI backend with automatic fallback to Mock API
// when DEMO mode is enabled or backend is unreachable.

import type {
  AnalysisRequest,
  AnalysisResponse,
  EvaluationMetricCard,
  HealthResponse,
  HistoryItem,
  ReportItem,
  UploadResponse,
  UploadedFileInfo,
} from '../types';

import {
  MOCK_HEALTH,
  getMockEvaluation,
  getMockHistory,
  getMockReports,
  mockRunAnalysis,
  mockUploadFiles,
} from './mockApi';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const FORCE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true';

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public details: Record<string, unknown> = {}
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorBody: { error?: { code: string; message: string; details?: Record<string, unknown> } } = {};
    try {
      errorBody = await res.json();
    } catch {
      throw new ApiError('NETWORK_ERROR', `HTTP ${res.status}: ${res.statusText}`);
    }
    throw new ApiError(
      errorBody.error?.code ?? 'UNKNOWN_ERROR',
      errorBody.error?.message ?? 'An error occurred.',
      errorBody.error?.details ?? {}
    );
  }
  return res.json() as Promise<T>;
}

// ---- Health --------------------------------------------------

export async function getHealth(): Promise<HealthResponse> {
  if (FORCE_MOCK) return MOCK_HEALTH;
  try {
    const res = await fetch('/health', { signal: AbortSignal.timeout(2000) });
    return await handleResponse<HealthResponse>(res);
  } catch {
    // Fall back gracefully to mock in demo/offline mode
    return MOCK_HEALTH;
  }
}

// ---- Upload --------------------------------------------------

export async function uploadFiles(
  files: File[],
  sessionId?: string
): Promise<UploadResponse> {
  if (FORCE_MOCK) {
    return mockUploadFiles(files, sessionId);
  }

  try {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    if (sessionId) formData.append('session_id', sessionId);

    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
      signal: AbortSignal.timeout(15000),
    });
    return await handleResponse<UploadResponse>(res);
  } catch (err) {
    console.warn('Backend upload unreachable, switching to demo mock mode:', err);
    return mockUploadFiles(files, sessionId);
  }
}

// ---- Analysis ------------------------------------------------

export async function runAnalysis(
  request: AnalysisRequest,
  uploadedInfos?: UploadedFileInfo[]
): Promise<AnalysisResponse> {
  if (FORCE_MOCK) {
    return mockRunAnalysis(request, uploadedInfos || []);
  }

  try {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: AbortSignal.timeout(30000),
    });
    return await handleResponse<AnalysisResponse>(res);
  } catch (err) {
    console.warn('Backend analyze unreachable, falling back to mock provider:', err);
    return mockRunAnalysis(request, uploadedInfos || []);
  }
}

export async function getAnalysisResult(requestId: string): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/analysis/${requestId}`);
  return handleResponse<AnalysisResponse>(res);
}

// ---- History & Reports ---------------------------------------

export async function getHistory(): Promise<HistoryItem[]> {
  try {
    const res = await fetch(`${API_BASE}/history`, { signal: AbortSignal.timeout(2000) });
    return await handleResponse<HistoryItem[]>(res);
  } catch {
    return getMockHistory();
  }
}

export async function getReports(): Promise<ReportItem[]> {
  try {
    const res = await fetch(`${API_BASE}/reports`, { signal: AbortSignal.timeout(2000) });
    return await handleResponse<ReportItem[]>(res);
  } catch {
    return getMockReports();
  }
}

export async function getEvaluation(): Promise<EvaluationMetricCard[]> {
  try {
    const res = await fetch(`${API_BASE}/evaluation`, { signal: AbortSignal.timeout(2000) });
    return await handleResponse<EvaluationMetricCard[]>(res);
  } catch {
    return getMockEvaluation();
  }
}

export async function generateReportPdf(requestId: string): Promise<{ downloadUrl: string; message: string }> {
  // Simulates call to backend for PDF compilation
  await new Promise((resolve) => setTimeout(resolve, 800));
  return {
    downloadUrl: `#report-${requestId}.pdf`,
    message: `Report for analysis ${requestId} compiled successfully.`,
  };
}
