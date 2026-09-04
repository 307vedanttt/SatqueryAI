// SatQuery AI — TypeScript API Types
// Mirrors the Pydantic schemas in backend/app/models/schemas.py

export type InputConfiguration =
  | 'SINGLE_OPTICAL'
  | 'SINGLE_SAR'
  | 'OPTICAL_SAR_PAIR'
  | 'BI_TEMPORAL'
  | 'UNKNOWN';

export type QueryIntent =
  | 'SCENE_DESCRIPTION'
  | 'VQA'
  | 'GROUNDING'
  | 'CHANGE_DESCRIPTION'
  | 'CHANGE_VQA'
  | 'OPTICAL_SAR_ANALYSIS'
  | 'BUILT_UP_ANALYSIS'
  | 'WATER_ANALYSIS'
  | 'OBJECT_IDENTIFICATION'
  | 'UNKNOWN';

export type AnalysisStatus =
  | 'pending'
  | 'processing'
  | 'success'
  | 'failed'
  | 'insufficient_evidence';

export type EvidenceType =
  | 'region'
  | 'bbox'
  | 'mask'
  | 'pixel_area'
  | 'metadata'
  | 'temporal_difference'
  | 'sensor_comparison'
  | 'model_prediction';

export type ConfidenceLabel = 'high' | 'medium' | 'low' | 'insufficient';

export type ExecutionStepStatus = 'success' | 'failed' | 'skipped' | 'in_progress';

// ---- Upload ----------------------------------------------------

export interface ImageMetadata {
  image_id: string;
  filename: string;
  width: number | null;
  height: number | null;
  bands: number | null;
  dtype: string | null;
  crs: string | null;
  resolution: [number, number] | null;
  bounds: [number, number, number, number] | null;
  nodata: number | null;
  driver: string | null;
  is_geotiff: boolean;
  sensor: string | null;
  acquisition_date: string | null;
  image_type: string | null;
}

export interface UploadedFileInfo {
  file_id: string;
  original_filename: string;
  internal_filename: string;
  size_bytes: number;
  extension: string;
  is_geotiff: boolean;
  metadata: ImageMetadata | null;
}

export interface UploadResponse {
  upload_id: string;
  session_id: string;
  files: UploadedFileInfo[];
  message: string;
}

// ---- Analysis --------------------------------------------------

export interface AnalysisRequest {
  session_id: string;
  upload_id: string;
  file_ids: string[];
  query: string;
}

export interface IntentResult {
  type: QueryIntent;
  confidence: number;
  reasoning: string | null;
  required_capabilities: string[];
}

export interface Evidence {
  evidence_id: string;
  specialist: string;
  source: string;
  claim: string;
  evidence_type: EvidenceType;
  region: Record<string, unknown> | null;
  bbox: [number, number, number, number] | null;
  date: string | null;
  sensor: string | null;
  confidence: number;
}

export interface ConfidenceBreakdown {
  input_score: number;
  specialist_score: number;
  evidence_score: number;
  agreement_score: number;
  final_score: number;
  label: ConfidenceLabel;
  explanation: string;
}

export interface DisagreementItem {
  source: string;
  claim: string;
  confidence: number;
}

export interface DisagreementResult {
  detected: boolean;
  items: DisagreementItem[];
  explanation: string | null;
}

export interface ExecutionStep {
  step_id: string;
  step_index: number;
  timestamp: string;
  action: string;
  component: string;
  status: ExecutionStepStatus;
  duration_ms: number | null;
  output_summary: string | null;
}

export interface AnswerBlock {
  text: string;
  is_refused: boolean;
  refusal_reason: string | null;
}

export interface AnalysisResponse {
  request_id: string;
  session_id: string;
  status: AnalysisStatus;
  input: { configuration: InputConfiguration; files: string[] };
  intent: IntentResult | null;
  answer: AnswerBlock;
  evidence: Evidence[];
  confidence: ConfidenceBreakdown | null;
  disagreement: DisagreementResult;
  execution_trace: ExecutionStep[];
  visual_outputs: Record<string, unknown>[];
  created_at: string | null;
  duration_ms: number | null;
}

// ---- Error -----------------------------------------------------

export interface ApiError {
  error: { code: string; message: string; details: Record<string, unknown> };
}

// ---- Health ----------------------------------------------------

export interface HealthResponse {
  status: string;
  version: string;
  app_name: string;
  demo_mode: boolean;
  database: string;
  timestamp: string;
  vision_provider: string;
  llm_provider: string;
}

// ---- Frontend UI & Navigation Types ----------------------------

export type NavigationTab = 'home' | 'workspace' | 'history' | 'reports' | 'evaluation' | 'about';

export type ViewMode = 'single' | 'side-by-side' | 'before-after' | 'difference';

export interface OverlayOptions {
  evidence: boolean;
  boundingBoxes: boolean;
  changeHeatmap: boolean;
  segmentation: boolean;
}

export interface ValidationItem {
  label: string;
  status: 'valid' | 'warning' | 'error' | 'pending';
  detail?: string;
}

export interface HistoryItem {
  id: string;
  requestId: string;
  query: string;
  task: string;
  configuration: InputConfiguration;
  confidenceScore: number;
  confidenceLabel: ConfidenceLabel;
  timestamp: string;
  fileCount: number;
  files: string[];
  answerSummary: string;
  result: AnalysisResponse;
}

export interface ReportItem {
  id: string;
  title: string;
  requestId: string;
  task: string;
  date: string;
  imageCount: number;
  confidenceScore: number;
  confidenceLabel: ConfidenceLabel;
  specialistUsed: string;
  summary: string;
  evidenceCount: number;
  result: AnalysisResponse;
}

export interface EvaluationMetricCard {
  task: string;
  metricName: string;
  metricValue: string | null;
  benchmarkTarget: string;
  status: 'active' | 'pending' | 'baseline';
  description: string;
}

