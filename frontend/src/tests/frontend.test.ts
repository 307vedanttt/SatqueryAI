import { describe, it, expect } from 'vitest';
import { generateMockMetadata, mockRunAnalysis, mockUploadFiles } from '../services/mockApi';
import { normalizeAnalysisResponse } from '../services/adapter';
import type { AnalysisRequest, UploadedFileInfo } from '../types';

describe('SatQuery AI Frontend Test Suite', () => {
  // ------------------------------------------------------------------------
  // 1. Upload & Metadata Tests
  // ------------------------------------------------------------------------
  describe('Upload & Metadata Service', () => {
    it('validates single optical upload and extracts GeoTIFF metadata', async () => {
      const mockFile = new File(['mock content'], 'sentinel2_scene.tif', { type: 'image/tiff' });
      const response = await mockUploadFiles([mockFile]);

      expect(response.upload_id).toBeDefined();
      expect(response.files).toHaveLength(1);
      const info = response.files[0];
      expect(info.is_geotiff).toBe(true);
      expect(info.metadata?.image_type).toBe('optical');
      expect(info.metadata?.crs).toBe('EPSG:32643');
    });

    it('validates two-image upload for optical + SAR pair', async () => {
      const f1 = new File(['opt'], 'sentinel2_optical.tif', { type: 'image/tiff' });
      const f2 = new File(['sar'], 'sentinel1_sar.tif', { type: 'image/tiff' });
      const response = await mockUploadFiles([f1, f2]);

      expect(response.files).toHaveLength(2);
      expect(response.files[0].metadata?.image_type).toBe('optical');
      expect(response.files[1].metadata?.image_type).toBe('sar');
    });

    it('generates consistent metadata for SAR and temporal files', () => {
      const sarMeta = generateMockMetadata('s1_grd_sar.tif');
      expect(sarMeta.image_type).toBe('sar');
      expect(sarMeta.sensor).toContain('Sentinel-1');

      const optMeta = generateMockMetadata('s2_t2_after_2025.tif');
      expect(optMeta.image_type).toBe('optical');
      expect(optMeta.acquisition_date).toBe('2025-08-21');
    });
  });

  // ------------------------------------------------------------------------
  // 2. Demo Scenario 1: Single Image VQA
  // ------------------------------------------------------------------------
  describe('Demo Scenario 1: Single Image VQA', () => {
    it('executes VQA and returns structured answer, confidence, and trace', async () => {
      const fileInfo: UploadedFileInfo = {
        file_id: 'f-1',
        original_filename: 'reservoir.tif',
        internal_filename: 'raw_reservoir.tif',
        size_bytes: 15000000,
        extension: 'tif',
        is_geotiff: true,
        metadata: generateMockMetadata('reservoir.tif'),
      };

      const request: AnalysisRequest = {
        session_id: 'sess-1',
        upload_id: 'up-1',
        file_ids: ['f-1'],
        query: 'What is visible in this image?',
      };

      const response = await mockRunAnalysis(request, [fileInfo]);

      expect(response.status).toBe('success');
      expect(response.input.configuration).toBe('SINGLE_OPTICAL');
      expect(response.answer.text).toContain('water reservoir');
      expect(response.confidence?.final_score).toBeGreaterThanOrEqual(0.75);
      expect(response.confidence?.label).toBe('high');
      expect(response.evidence.length).toBeGreaterThan(0);
      expect(response.execution_trace.length).toBe(5);
    });
  });

  // ------------------------------------------------------------------------
  // 3. Demo Scenario 2: Spatial Grounding (Bounding Boxes)
  // ------------------------------------------------------------------------
  describe('Demo Scenario 2: Spatial Grounding', () => {
    it('returns pixel-space bounding boxes for region grounding queries', async () => {
      const fileInfo: UploadedFileInfo = {
        file_id: 'f-2',
        original_filename: 'urban_complex.tif',
        internal_filename: 'raw_urban.tif',
        size_bytes: 12000000,
        extension: 'tif',
        is_geotiff: true,
        metadata: generateMockMetadata('urban_complex.tif'),
      };

      const request: AnalysisRequest = {
        session_id: 'sess-2',
        upload_id: 'up-2',
        file_ids: ['f-2'],
        query: 'Where are the buildings?',
      };

      const response = await mockRunAnalysis(request, [fileInfo]);

      expect(response.intent?.type).toBe('GROUNDING');
      expect(response.evidence.some((ev) => ev.evidence_type === 'bbox')).toBe(true);

      const bboxEv = response.evidence.find((ev) => ev.bbox !== null);
      expect(bboxEv).toBeDefined();
      expect(bboxEv?.bbox).toHaveLength(4);
      const [x1, y1, x2, y2] = bboxEv!.bbox!;
      expect(x1).toBeLessThan(x2);
      expect(y1).toBeLessThan(y2);
    });
  });

  // ------------------------------------------------------------------------
  // 4. Demo Scenario 3: Optical + SAR Fusion
  // ------------------------------------------------------------------------
  describe('Demo Scenario 3: Optical + SAR Fusion & Disagreement', () => {
    it('detects complementary sensor signals and flags cross-sensor disagreement', async () => {
      const optInfo: UploadedFileInfo = {
        file_id: 'f-opt',
        original_filename: 'tile_optical.tif',
        internal_filename: 'raw_opt.tif',
        size_bytes: 14000000,
        extension: 'tif',
        is_geotiff: true,
        metadata: generateMockMetadata('tile_optical.tif'),
      };

      const sarInfo: UploadedFileInfo = {
        file_id: 'f-sar',
        original_filename: 'tile_sar_intensity.tif',
        internal_filename: 'raw_sar.tif',
        size_bytes: 8000000,
        extension: 'tif',
        is_geotiff: true,
        metadata: generateMockMetadata('tile_sar_intensity.tif'),
      };

      const request: AnalysisRequest = {
        session_id: 'sess-3',
        upload_id: 'up-3',
        file_ids: ['f-opt', 'f-sar'],
        query: 'What complementary information do these sensors provide?',
      };

      const response = await mockRunAnalysis(request, [optInfo, sarInfo]);

      expect(response.input.configuration).toBe('OPTICAL_SAR_PAIR');
      expect(response.intent?.type).toBe('OPTICAL_SAR_ANALYSIS');
      expect(response.disagreement.detected).toBe(true);
      expect(response.disagreement.items.length).toBeGreaterThan(0);
      expect(response.evidence.some((e) => e.evidence_type === 'sensor_comparison')).toBe(true);
      expect(response.confidence?.label).toBe('medium');
    });
  });

  // ------------------------------------------------------------------------
  // 5. Demo Scenario 4: Bi-Temporal Change Detection
  // ------------------------------------------------------------------------
  describe('Demo Scenario 4: Bi-Temporal Change Detection', () => {
    it('executes bi-temporal differencing and returns temporal change evidence', async () => {
      const t1Info: UploadedFileInfo = {
        file_id: 'f-t1',
        original_filename: 'sentinel_t1_2024.tif',
        internal_filename: 'raw_t1.tif',
        size_bytes: 14000000,
        extension: 'tif',
        is_geotiff: true,
        metadata: generateMockMetadata('sentinel_t1_2024.tif'),
      };

      const t2Info: UploadedFileInfo = {
        file_id: 'f-t2',
        original_filename: 'sentinel_t2_2025_after.tif',
        internal_filename: 'raw_t2.tif',
        size_bytes: 14000000,
        extension: 'tif',
        is_geotiff: true,
        metadata: generateMockMetadata('sentinel_t2_2025_after.tif'),
      };

      const request: AnalysisRequest = {
        session_id: 'sess-4',
        upload_id: 'up-4',
        file_ids: ['f-t1', 'f-t2'],
        query: 'What changed between these images?',
      };

      const response = await mockRunAnalysis(request, [t1Info, t2Info]);

      expect(response.input.configuration).toBe('BI_TEMPORAL');
      expect(response.answer.text).toContain('Bi-temporal comparative analysis');
      expect(response.evidence.some((e) => e.evidence_type === 'temporal_difference')).toBe(true);
      expect(response.confidence?.label).toBe('high');
    });
  });

  // ------------------------------------------------------------------------
  // 6. Response Adapter Normalization
  // ------------------------------------------------------------------------
  describe('Response Adapter Layer', () => {
    it('normalizes backend response into resilient UI view model', async () => {
      const fileInfo: UploadedFileInfo = {
        file_id: 'f-adapt',
        original_filename: 'tile.tif',
        internal_filename: 'raw_tile.tif',
        size_bytes: 10000000,
        extension: 'tif',
        is_geotiff: true,
        metadata: generateMockMetadata('tile.tif'),
      };

      const rawResponse = await mockRunAnalysis(
        {
          session_id: 'sess-adapt',
          upload_id: 'up-adapt',
          file_ids: ['f-adapt'],
          query: 'Describe this scene',
        },
        [fileInfo]
      );

      const viewModel = normalizeAnalysisResponse(rawResponse);

      expect(viewModel.taskTitle).toBe('Scene Description');
      expect(viewModel.answerText).toBeDefined();
      expect(viewModel.confidenceScore).toBeGreaterThan(0);
      expect(viewModel.evidence).toBeInstanceOf(Array);
      expect(viewModel.executionTrace).toHaveLength(5);
    });
  });
});
