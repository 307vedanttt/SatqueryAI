// SatQuery AI — Typed API Client
// All calls go through FastAPI backend — never directly to external providers.

import type {
  AnalysisRequest,
  AnalysisResponse,
  HealthResponse,
  UploadResponse,
} from '../types';

const API_BASE = '/api/v1';

class ApiError extends Error {
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
    let errorBody: { error?: { code: string; message: string } } = {};
    try {
      errorBody = await res.json();
    } catch {
      throw new ApiError('NETWORK_ERROR', `HTTP ${res.status}: ${res.statusText}`);
    }
    throw new ApiError(
      errorBody.error?.code ?? 'UNKNOWN_ERROR',
      errorBody.error?.message ?? 'An error occurred.'
    );
  }
  return res.json() as Promise<T>;
}

// ---- Health --------------------------------------------------

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch('/health');
  return handleResponse<HealthResponse>(res);
}

// ---- Upload --------------------------------------------------

export async function uploadFiles(
  files: File[],
  sessionId?: string
): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((f) => formData.append('files', f));
  if (sessionId) formData.append('session_id', sessionId);

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<UploadResponse>(res);
}

// ---- Analysis ------------------------------------------------

export async function runAnalysis(
  request: AnalysisRequest
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<AnalysisResponse>(res);
}

export async function getAnalysisResult(requestId: string): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/analysis/${requestId}`);
  return handleResponse<AnalysisResponse>(res);
}

export { ApiError };
