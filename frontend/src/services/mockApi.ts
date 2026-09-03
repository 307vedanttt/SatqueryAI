// SatQuery AI — Realistic Mock API Service
// Demonstrates all 4 primary multimodal workflows:
//   1. Single Image VQA
//   2. Grounding (Bounding Boxes)
//   3. Optical + SAR Fusion (Sensor Comparison & Disagreement)
//   4. Bi-Temporal Change Detection (Temporal Differencing)

import type {
  AnalysisRequest,
  AnalysisResponse,
  ConfidenceBreakdown,
  DisagreementResult,
  EvaluationMetricCard,
  Evidence,
  ExecutionStep,
  HealthResponse,
  HistoryItem,
  ImageMetadata,
  InputConfiguration,
  QueryIntent,
  ReportItem,
  UploadResponse,
  UploadedFileInfo,
} from '../types';

export const MOCK_HEALTH: HealthResponse = {
  status: 'ok',
  version: '0.1.0',
  app_name: 'SatQuery AI',
  demo_mode: true,
  database: 'sqlite:///data/satquery.db',
  timestamp: new Date().toISOString(),
  vision_provider: 'mock-multimodal-v1',
  llm_provider: 'mock-llm-v1',
};

// --- Mock Metadata Generator ---

export function generateMockMetadata(filename: string, index: number = 0): ImageMetadata {
  const isSar =
    filename.toLowerCase().includes('sar') ||
    filename.toLowerCase().includes('s1') ||
    filename.toLowerCase().includes('radar');

  const isAfter =
    filename.toLowerCase().includes('after') ||
    filename.toLowerCase().includes('t2') ||
    filename.toLowerCase().includes('2025');

  return {
    image_id: `img-${index + 1}-${Math.random().toString(36).substring(2, 8)}`,
    filename,
    width: 1920,
    height: 1080,
    bands: isSar ? 1 : 4,
    dtype: isSar ? 'float32' : 'uint16',
    crs: 'EPSG:32643',
    resolution: [10.0, 10.0],
    bounds: [450000.0, 3100000.0, 469200.0, 3110800.0],
    nodata: 0.0,
    driver: 'GTiff',
    is_geotiff: filename.toLowerCase().endsWith('.tif') || filename.toLowerCase().endsWith('.tiff'),
    sensor: isSar ? 'Sentinel-1 C-SAR' : 'Sentinel-2 MSI',
    acquisition_date: isAfter ? '2025-08-21' : isSar ? '2025-03-12' : '2024-03-15',
    image_type: isSar ? 'sar' : 'optical',
  };
}

// --- Mock Upload Handler ---

export async function mockUploadFiles(
  files: File[],
  sessionId?: string
): Promise<UploadResponse> {
  await new Promise((resolve) => setTimeout(resolve, 600));

  const sid = sessionId || `session-${Math.random().toString(36).substring(2, 9)}`;
  const uploadId = `upload-${Math.random().toString(36).substring(2, 9)}`;

  const uploadedFiles: UploadedFileInfo[] = files.map((file, idx) => {
    const isGeo = file.name.toLowerCase().endsWith('.tif') || file.name.toLowerCase().endsWith('.tiff');
    return {
      file_id: `file-${idx + 1}-${Date.now().toString(36)}`,
      original_filename: file.name,
      internal_filename: `raw_${idx + 1}_${file.name}`,
      size_bytes: file.size || 14200000,
      extension: file.name.split('.').pop() || 'tif',
      is_geotiff: isGeo,
      metadata: generateMockMetadata(file.name, idx),
    };
  });

  return {
    upload_id: uploadId,
    session_id: sid,
    files: uploadedFiles,
    message: `Successfully validated and registered ${files.length} imagery file(s).`,
  };
}

// --- Mock Analysis Pipeline ---

export async function mockRunAnalysis(
  request: AnalysisRequest,
  fileInfos: UploadedFileInfo[]
): Promise<AnalysisResponse> {
  // Simulate end-to-end multi-step inference delay
  await new Promise((resolve) => setTimeout(resolve, 1400));

  const queryLower = request.query.toLowerCase();
  const fileCount = fileInfos.length;

  const hasSar = fileInfos.some((f) => f.metadata?.image_type === 'sar');
  const hasOptical = fileInfos.some((f) => f.metadata?.image_type === 'optical');
  const isOpticalSarPair = fileCount === 2 && hasSar && hasOptical;

  const isBitemporal =
    fileCount === 2 &&
    !isOpticalSarPair &&
    fileInfos[0].metadata?.acquisition_date !== fileInfos[1].metadata?.acquisition_date;

  // Determine Scenario
  let config: InputConfiguration = 'SINGLE_OPTICAL';
  let intent: QueryIntent = 'VQA';
  let specialist = 'vqa';
  let answerText = '';
  let evidenceList: Evidence[] = [];
  let disagreement: DisagreementResult = { detected: false, items: [], explanation: null };
  let confidence: ConfidenceBreakdown;

  if (fileCount === 1) {
    if (
      queryLower.includes('where') ||
      queryLower.includes('locate') ||
      queryLower.includes('ground') ||
      queryLower.includes('box')
    ) {
      // Scenario 2: Grounding
      config = fileInfos[0].metadata?.image_type === 'sar' ? 'SINGLE_SAR' : 'SINGLE_OPTICAL';
      intent = 'GROUNDING';
      specialist = 'grounding';
      answerText =
        "The requested target features have been localized in image pixel coordinates. " +
        "Prominent built-up structures and commercial facilities are concentrated in the southwestern sector [320, 240, 890, 780]. " +
        "The adjacent transport corridor was localized at [150, 480, 720, 620].";
      evidenceList = [
        {
          evidence_id: 'ev-ground-1',
          specialist: 'grounding',
          source: 'grounding_detector',
          claim: 'Built-up commercial complex localized',
          evidence_type: 'bbox',
          bbox: [320, 240, 890, 780],
          region: null,
          date: fileInfos[0].metadata?.acquisition_date || null,
          sensor: fileInfos[0].metadata?.sensor || 'Sentinel-2',
          confidence: 0.91,
        },
        {
          evidence_id: 'ev-ground-2',
          specialist: 'grounding',
          source: 'grounding_detector',
          claim: 'Arterial access roadway localized',
          evidence_type: 'bbox',
          bbox: [150, 480, 720, 620],
          region: null,
          date: fileInfos[0].metadata?.acquisition_date || null,
          sensor: fileInfos[0].metadata?.sensor || 'Sentinel-2',
          confidence: 0.85,
        },
      ];
      confidence = {
        input_score: 0.95,
        specialist_score: 0.88,
        evidence_score: 0.9,
        agreement_score: 1.0,
        final_score: 0.89,
        label: 'high',
        explanation: 'High confidence: image space features cleanly match localized bounding coordinates with verified CRS alignment.',
      };
    } else {
      // Scenario 1: Single Image VQA / Scene Description
      config = fileInfos[0].metadata?.image_type === 'sar' ? 'SINGLE_SAR' : 'SINGLE_OPTICAL';
      intent = 'SCENE_DESCRIPTION';
      specialist = 'vqa';
      answerText =
        "The imagery reveals a heterogeneous regional landscape. A prominent open water reservoir occupies " +
        "approximately 34% of the central surface area. Dense broadleaf vegetation borders the northern shoreline, " +
        "transitioning into agricultural plots toward the east. Built-up settlement clusters are visible in the southwestern quadrant.";
      evidenceList = [
        {
          evidence_id: 'ev-vqa-1',
          specialist: 'vqa',
          source: 'optical_vision_model',
          claim: 'Central water reservoir coverage ~34%',
          evidence_type: 'bbox',
          bbox: [380, 280, 1150, 880],
          region: null,
          date: fileInfos[0].metadata?.acquisition_date || '2024-03-15',
          sensor: 'Sentinel-2 MSI',
          confidence: 0.88,
        },
        {
          evidence_id: 'ev-vqa-2',
          specialist: 'vqa',
          source: 'optical_vision_model',
          claim: 'Dense vegetation canopy along northern sector',
          evidence_type: 'region',
          bbox: [0, 0, 1920, 400],
          region: null,
          date: fileInfos[0].metadata?.acquisition_date || '2024-03-15',
          sensor: 'Sentinel-2 MSI',
          confidence: 0.82,
        },
      ];
      confidence = {
        input_score: 0.9,
        specialist_score: 0.85,
        evidence_score: 0.84,
        agreement_score: 1.0,
        final_score: 0.87,
        label: 'high',
        explanation: 'High confidence: clear single-sensor optical scene with well-delineated spectral signatures.',
      };
    }
  } else if (isOpticalSarPair) {
    // Scenario 3: Optical + SAR Fusion
    config = 'OPTICAL_SAR_PAIR';
    intent = 'OPTICAL_SAR_ANALYSIS';
    specialist = 'mock_optical_sar';
    answerText =
      "Optical analysis reveals high spectral reflectance in the northern sector consistent with bare soil or low vegetation. " +
      "However, SAR backscatter analysis of the identical coordinates exhibits pronounced double-bounce dielectric returns, " +
      "strongly indicating vertical metallic or masonry structures (dense urban development). " +
      "The central water reservoir is confirmed by both modalities (low optical reflectance and specular radar null).";
    disagreement = {
      detected: true,
      items: [
        { source: 'optical_channel', claim: 'Northern sector: bare soil / sparse scrub', confidence: 0.72 },
        { source: 'sar_channel', claim: 'Northern sector: strong double-bounce (dense structures)', confidence: 0.84 },
      ],
      explanation:
        'Optical spectral response indicates bare terrain, while SAR backscatter indicates vertical structures. Ground verification is recommended.',
    };
    evidenceList = [
      {
        evidence_id: 'ev-opt-1',
        specialist: 'mock_optical_sar',
        source: 'optical_channel',
        claim: 'Northern sector: moderate reflectance, low NDVI',
        evidence_type: 'sensor_comparison',
        bbox: [0, 0, 1920, 480],
        region: null,
        date: '2025-03-12',
        sensor: 'Sentinel-2 Optical',
        confidence: 0.72,
      },
      {
        evidence_id: 'ev-sar-1',
        specialist: 'mock_optical_sar',
        source: 'sar_channel',
        claim: 'Northern sector: intense double-bounce backscatter (vertical roughness)',
        evidence_type: 'sensor_comparison',
        bbox: [0, 0, 1920, 480],
        region: null,
        date: '2025-03-12',
        sensor: 'Sentinel-1 C-SAR',
        confidence: 0.84,
      },
      {
        evidence_id: 'ev-joint-1',
        specialist: 'mock_optical_sar',
        source: 'fusion',
        claim: 'Central water body verified by both specular radar and optical absorption',
        evidence_type: 'bbox',
        bbox: [380, 280, 1150, 880],
        region: null,
        date: '2025-03-12',
        sensor: 'Optical + SAR Joint',
        confidence: 0.94,
      },
    ];
    confidence = {
      input_score: 0.92,
      specialist_score: 0.78,
      evidence_score: 0.85,
      agreement_score: 0.65,
      final_score: 0.76,
      label: 'medium',
      explanation: 'Moderate confidence: sensor contradiction detected in northern quadrant reduces overall agreement score.',
    };
  } else {
    // Scenario 4: Bi-temporal Change Detection
    config = isBitemporal ? 'BI_TEMPORAL' : 'BI_TEMPORAL';
    intent = 'CHANGE_DESCRIPTION';
    specialist = 'mock_change_detection';
    answerText =
      "Bi-temporal comparative analysis between T1 (2024-03-15) and T2 (2025-08-21) detects 3 significant land-cover transformations:\n\n" +
      "1. **Built-up expansion (northwest quadrant):** ~2.4 km² of new residential/industrial structures appeared.\n" +
      "2. **Vegetation loss (eastern sector):** ~1.1 km² of dense tree canopy cleared.\n" +
      "3. **Water reservoir boundary variation:** Minor southward perimeter shift (-0.3 km²) indicating seasonal fluctuation.";
    evidenceList = [
      {
        evidence_id: 'ev-chg-1',
        specialist: 'mock_change_detection',
        source: 'temporal_differencing',
        claim: 'New built-up structural footprints in NW sector',
        evidence_type: 'temporal_difference',
        bbox: [50, 40, 680, 520],
        region: null,
        date: '2025-08-21',
        sensor: 'Sentinel-2 MSI',
        confidence: 0.89,
      },
      {
        evidence_id: 'ev-chg-2',
        specialist: 'mock_change_detection',
        source: 'temporal_differencing',
        claim: 'Vegetation canopy loss in eastern sector',
        evidence_type: 'temporal_difference',
        bbox: [1150, 180, 1880, 860],
        region: null,
        date: '2025-08-21',
        sensor: 'Sentinel-2 MSI',
        confidence: 0.84,
      },
      {
        evidence_id: 'ev-chg-3',
        specialist: 'mock_change_detection',
        source: 'temporal_differencing',
        claim: 'Reservoir margin seasonal drawdown',
        evidence_type: 'temporal_difference',
        bbox: [380, 280, 1150, 880],
        region: null,
        date: '2025-08-21',
        sensor: 'Sentinel-2 MSI',
        confidence: 0.79,
      },
    ];
    confidence = {
      input_score: 0.95,
      specialist_score: 0.86,
      evidence_score: 0.88,
      agreement_score: 1.0,
      final_score: 0.88,
      label: 'high',
      explanation: 'High confidence: bi-temporal imagery verified with matching coordinate reference system (EPSG:32643) and <1% spatial drift.',
    };
  }

  // Generate complete execution trace
  const now = Date.now();
  const traceSteps: ExecutionStep[] = [
    {
      step_id: 'trace-1',
      step_index: 1,
      timestamp: new Date(now - 1200).toISOString(),
      action: 'Validate input imagery',
      component: 'alignment_validator',
      status: 'success',
      duration_ms: 110,
      output_summary: `Validated ${fileCount} file(s): GeoTIFF CRS and bounds aligned.`,
    },
    {
      step_id: 'trace-2',
      step_index: 2,
      timestamp: new Date(now - 1050).toISOString(),
      action: 'Detect configuration',
      component: 'configuration_classifier',
      status: 'success',
      duration_ms: 45,
      output_summary: `Detected configuration: ${config}`,
    },
    {
      step_id: 'trace-3',
      step_index: 3,
      timestamp: new Date(now - 980).toISOString(),
      action: 'Understand query intent',
      component: 'intent_planner',
      status: 'success',
      duration_ms: 65,
      output_summary: `Classified intent: ${intent}`,
    },
    {
      step_id: 'trace-4',
      step_index: 4,
      timestamp: new Date(now - 900).toISOString(),
      action: `Execute specialist: ${specialist}`,
      component: specialist,
      status: 'success',
      duration_ms: 480,
      output_summary: `Executed ${specialist} model. Generated ${evidenceList.length} evidence claims.`,
    },
    {
      step_id: 'trace-5',
      step_index: 5,
      timestamp: new Date(now - 400).toISOString(),
      action: 'Synthesize evidence & assess confidence',
      component: 'confidence_calculator',
      status: disagreement.detected ? 'success' : 'success',
      duration_ms: 120,
      output_summary: `Confidence calculated: ${(confidence.final_score * 100).toFixed(0)}% (${confidence.label.toUpperCase()})`,
    },
  ];

  return {
    request_id: `req-${Date.now().toString(36)}`,
    session_id: request.session_id,
    status: 'success',
    input: {
      configuration: config,
      files: fileInfos.map((f) => f.original_filename),
    },
    intent: {
      type: intent,
      confidence: 0.92,
      reasoning: `Matched query intent to ${intent} under configuration ${config}.`,
      required_capabilities: [specialist],
    },
    answer: {
      text: answerText,
      is_refused: false,
      refusal_reason: null,
    },
    evidence: evidenceList,
    confidence,
    disagreement,
    execution_trace: traceSteps,
    visual_outputs: [],
    created_at: new Date().toISOString(),
    duration_ms: 820,
  };
}

// --- Mock History & Reports ---

export function getMockHistory(): HistoryItem[] {
  return [
    {
      id: 'hist-1',
      requestId: 'req-hist-001',
      query: 'What changed between the two acquisition dates?',
      task: 'Bi-Temporal Change Detection',
      configuration: 'BI_TEMPORAL',
      confidenceScore: 0.88,
      confidenceLabel: 'high',
      timestamp: '2026-09-03T10:15:00Z',
      fileCount: 2,
      files: ['sentinel2_t1_2024.tif', 'sentinel2_t2_2025.tif'],
      answerSummary: '3 significant change clusters detected: built-up expansion in northwest and vegetation clearing.',
      result: {} as AnalysisResponse,
    },
    {
      id: 'hist-2',
      requestId: 'req-hist-002',
      query: 'What complementary insights do optical and SAR imagery provide?',
      task: 'Optical + SAR Fusion Analysis',
      configuration: 'OPTICAL_SAR_PAIR',
      confidenceScore: 0.76,
      confidenceLabel: 'medium',
      timestamp: '2026-09-03T09:40:00Z',
      fileCount: 2,
      files: ['sentinel2_optical.tif', 'sentinel1_sar_vv.tif'],
      answerSummary: 'Cross-sensor divergence flagged in northern sector: optical shows bare soil while SAR detects double-bounce structures.',
      result: {} as AnalysisResponse,
    },
    {
      id: 'hist-3',
      requestId: 'req-hist-003',
      query: 'Where are the primary commercial building complexes located?',
      task: 'Spatial Grounding',
      configuration: 'SINGLE_OPTICAL',
      confidenceScore: 0.91,
      confidenceLabel: 'high',
      timestamp: '2026-09-02T16:22:00Z',
      fileCount: 1,
      files: ['bangalore_urban_tile.tif'],
      answerSummary: 'Localized commercial complexes at [320, 240, 890, 780] in pixel space.',
      result: {} as AnalysisResponse,
    },
    {
      id: 'hist-4',
      requestId: 'req-hist-004',
      query: 'Describe the dominant land cover and surface features.',
      task: 'Single-Image Scene Description',
      configuration: 'SINGLE_OPTICAL',
      confidenceScore: 0.87,
      confidenceLabel: 'high',
      timestamp: '2026-09-01T11:05:00Z',
      fileCount: 1,
      files: ['reservoir_surroundings.tif'],
      answerSummary: 'Identified central water body (34%), northern broadleaf vegetation (41%), and southwestern settlement (18%).',
      result: {} as AnalysisResponse,
    },
  ];
}

export function getMockReports(): ReportItem[] {
  return [
    {
      id: 'rep-1',
      title: 'Bi-Temporal Urban Expansion Assessment Report',
      requestId: 'req-hist-001',
      task: 'Change Detection',
      date: 'September 3, 2026',
      imageCount: 2,
      confidenceScore: 0.88,
      confidenceLabel: 'high',
      specialistUsed: 'Change Detection Specialist',
      summary: 'Comparative analysis across 2 GeoTIFF tiles identified 2.4 km² urban footprint growth and 1.1 km² canopy reduction.',
      evidenceCount: 3,
      result: {} as AnalysisResponse,
    },
    {
      id: 'rep-2',
      title: 'Multimodal Sensor Fusion & Disagreement Analysis',
      requestId: 'req-hist-002',
      task: 'Optical + SAR Fusion',
      date: 'September 3, 2026',
      imageCount: 2,
      confidenceScore: 0.76,
      confidenceLabel: 'medium',
      specialistUsed: 'Optical-SAR Fusion Specialist',
      summary: 'Co-registered Sentinel-1 C-SAR and Sentinel-2 MSI analysis. Flagged structural contradiction for northern quad.',
      evidenceCount: 3,
      result: {} as AnalysisResponse,
    },
    {
      id: 'rep-3',
      title: 'Automated Regional Land Cover Delineation Summary',
      requestId: 'req-hist-004',
      task: 'Scene Description',
      date: 'September 1, 2026',
      imageCount: 1,
      confidenceScore: 0.87,
      confidenceLabel: 'high',
      specialistUsed: 'VQA & Scene Description Specialist',
      summary: 'Automated categorical land cover decomposition with verified bbox evidence for lake perimeter and forest tract.',
      evidenceCount: 2,
      result: {} as AnalysisResponse,
    },
  ];
}

export function getMockEvaluation(): EvaluationMetricCard[] {
  return [
    {
      task: 'Single-Image VQA',
      metricName: 'Accuracy / BLEU-4',
      metricValue: '82.4%',
      benchmarkTarget: '≥ 80.0%',
      status: 'active',
      description: 'Evaluated against multi-class land-use and object query validation sets.',
    },
    {
      task: 'Region Grounding',
      metricName: 'Mean IoU @ 0.5',
      metricValue: '0.742',
      benchmarkTarget: '≥ 0.700',
      status: 'active',
      description: 'Intersection over Union for text-prompted spatial bounding box localization.',
    },
    {
      task: 'Change Detection',
      metricName: 'F1-Score / IoU',
      metricValue: '0.865',
      benchmarkTarget: '≥ 0.850',
      status: 'active',
      description: 'Pixel-level and parcel-level bi-temporal binary change delineation.',
    },
    {
      task: 'Router & Classifier',
      metricName: 'Routing Precision',
      metricValue: '96.8%',
      benchmarkTarget: '≥ 95.0%',
      status: 'active',
      description: 'Deterministic accuracy of configuration identification and intent routing.',
    },
    {
      task: 'System Orchestration',
      metricName: 'Average Pipeline Latency',
      metricValue: '840 ms',
      benchmarkTarget: '< 2000 ms',
      status: 'active',
      description: 'End-to-end processing duration from upload validation to trace generation in demo mode.',
    },
  ];
}
