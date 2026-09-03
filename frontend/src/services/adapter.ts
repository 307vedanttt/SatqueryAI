// SatQuery AI — Backend Response Adapter
// Normalizes responses into consistent UI view models, protecting components
// from contract variances between backend versions or mock data.

import type {
  AnalysisResponse,
  ConfidenceLabel,
  Evidence,
  ExecutionStep,
  InputConfiguration,
} from '../types';

export interface NormalizedEvidenceItem {
  id: string;
  source: string;
  claim: string;
  type: string;
  confidence: number;
  bbox: [number, number, number, number] | null;
  date: string | null;
  sensor: string | null;
}

export interface NormalizedAnalysisView {
  requestId: string;
  sessionId: string;
  status: string;
  configuration: InputConfiguration;
  intentType: string;
  taskTitle: string;
  answerText: string;
  isRefused: boolean;
  refusalReason: string | null;
  confidenceScore: number;
  confidenceLabel: ConfidenceLabel;
  confidenceExplanation: string;
  disagreementDetected: boolean;
  disagreementExplanation: string | null;
  disagreementItems: Array<{ source: string; claim: string; confidence: number }>;
  evidence: NormalizedEvidenceItem[];
  executionTrace: ExecutionStep[];
  durationMs: number | null;
  createdAt: string | null;
}

export function normalizeAnalysisResponse(response: AnalysisResponse): NormalizedAnalysisView {
  const config = response.input?.configuration || 'UNKNOWN';
  const intentType = response.intent?.type || 'UNKNOWN';

  let taskTitle = 'Remote Sensing Analysis';
  if (config === 'BI_TEMPORAL') {
    taskTitle = 'Bi-Temporal Change Detection';
  } else if (config === 'OPTICAL_SAR_PAIR') {
    taskTitle = 'Optical + SAR Cross-Modal Fusion';
  } else if (intentType === 'GROUNDING') {
    taskTitle = 'Spatial Region Grounding';
  } else if (intentType === 'SCENE_DESCRIPTION') {
    taskTitle = 'Scene Description';
  } else if (intentType === 'VQA') {
    taskTitle = 'Single-Image Visual Question Answering';
  }

  const normEvidence: NormalizedEvidenceItem[] = (response.evidence || []).map((ev: Evidence, idx: number) => ({
    id: ev.evidence_id || `ev-${idx}`,
    source: ev.source || ev.specialist || 'Specialist Model',
    claim: ev.claim || 'Observation recorded',
    type: ev.evidence_type || 'model_prediction',
    confidence: typeof ev.confidence === 'number' ? ev.confidence : 0.8,
    bbox: Array.isArray(ev.bbox) && ev.bbox.length === 4 ? ev.bbox : null,
    date: ev.date || null,
    sensor: ev.sensor || null,
  }));

  const confScore = response.confidence?.final_score ?? 0.8;
  const confLabel = response.confidence?.label ?? (confScore >= 0.75 ? 'high' : confScore >= 0.4 ? 'medium' : 'low');
  const confExpl = response.confidence?.explanation ?? 'Confidence calculated from input alignment and evidence consistency.';

  return {
    requestId: response.request_id || 'unknown',
    sessionId: response.session_id || 'unknown',
    status: response.status || 'success',
    configuration: config,
    intentType,
    taskTitle,
    answerText: response.answer?.text || 'No answer generated.',
    isRefused: Boolean(response.answer?.is_refused),
    refusalReason: response.answer?.refusal_reason || null,
    confidenceScore: confScore,
    confidenceLabel: confLabel,
    confidenceExplanation: confExpl,
    disagreementDetected: Boolean(response.disagreement?.detected),
    disagreementExplanation: response.disagreement?.explanation || null,
    disagreementItems: response.disagreement?.items || [],
    evidence: normEvidence,
    executionTrace: response.execution_trace || [],
    durationMs: response.duration_ms || null,
    createdAt: response.created_at || null,
  };
}
