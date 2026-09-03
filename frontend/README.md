# SatQuery AI — Frontend Workstation

Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries.

Developed for **Smart India Hackathon 2026 (Problem Statement SIH26167)** — **ISRO Department of Space**.

---

## 1. Project Overview

SatQuery AI is an aerospace-inspired remote-sensing analysis workstation. Rather than functioning as an unconstrained chatbot, it implements a **bounded orchestration pipeline**:

```text
UPLOAD IMAGERY → VALIDATE INPUT → UNDERSTAND QUERY → SELECT SPECIALIST → RUN ANALYSIS → COLLECT EVIDENCE → CHECK CONFIDENCE → GENERATE ANSWER → SHOW EXECUTION TRACE
```

### Key Capabilities

- **Single-Image VQA & Scene Description:** Natural language analysis of land cover, water bodies, and infrastructure.
- **Text-Guided Spatial Grounding:** Localizes queried objects returning verified bounding boxes `[x1, y1, x2, y2]` in image-pixel space.
- **Optical + SAR Multimodal Fusion:** Combines multispectral reflectance with synthetic aperture radar dielectric roughness, surfacing cross-sensor contradictions.
- **Bi-Temporal Change Detection:** Compares co-registered acquisition dates to detect built-up expansion, deforestation, and water margin shifts.

---

## 2. Technology Stack

- **Framework:** React 18 with TypeScript
- **Bundler:** Vite 5
- **Testing:** Vitest
- **Styling:** Custom Aerospace Design System with Glassmorphism (`index.css`)
- **API Architecture:** Typed API Client with resilient Response Adapter and Mock Fallback

---

## 3. Project Structure

```text
frontend/
├── src/
│   ├── components/
│   │   ├── layout/         # Header, Footer, Navigation
│   │   ├── upload/         # UploadZone, ValidationPanel, ConfigurationCard
│   │   ├── viewer/         # ImageViewer (Zoom/Pan/Split/Side-by-side), Overlays, Legends
│   │   ├── metadata/       # MetadataCard
│   │   ├── analysis/       # QuerySection, SuggestedQuestions, Progress, ResponsePanel
│   │   ├── evidence/       # EvidencePanel (Categorized, Expandable, "View on image")
│   │   ├── trace/          # ExecutionTrace (Collapsible, numbered steps)
│   │   └── common/         # ConfidenceBadge, StatusBadges
│   ├── pages/
│   │   ├── Workspace.tsx   # 3-Column Analysis Interface + Quick-Launch Presets
│   │   ├── History.tsx     # Historical Audit Trail with Filtering & Search
│   │   ├── Reports.tsx     # Scientific Mission Summaries & PDF Export
│   │   ├── Evaluation.tsx  # Quantitative Benchmark Dashboard
│   │   └── About.tsx       # System Architecture & Bounded Planner Rationale
│   ├── services/
│   │   ├── api.ts          # Typed Backend Client
│   │   ├── mockApi.ts      # Offline Multi-Scenario Demo Engine
│   │   └── adapter.ts      # UI Response Normalizer
│   ├── types/
│   │   └── index.ts        # Shared Pydantic Contract Mirrors
│   ├── tests/
│   │   └── frontend.test.ts # Vitest Test Suite
│   ├── App.tsx             # Root Application Shell
│   ├── main.tsx            # Entry Point
│   └── index.css           # Global Design System
├── public/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## 4. Installation & Development

### Prerequisites

- Node.js (v18+)
- npm (v9+)

### Installation

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

The application will start at `http://localhost:5173`.

### Run Test Suite

```bash
npm run test
```

### Compile Production Build

```bash
npm run build
```

The production assets will be output to `dist/`.

---

## 5. Environment Variables & Modes

Configuration is managed via `.env.example`:

```env
# Backend API Base URL (leave empty for same-origin proxy '/api/v1')
VITE_API_BASE_URL=

# Force Mock Demo API (true = offline demo mode, false = real FastAPI backend)
VITE_USE_MOCK_API=false
```

> **Security Note:** API keys and provider secrets are NEVER placed in frontend environment variables. All requests route through the FastAPI backend.

---

## 6. Demo Presets (One-Click Scenarios)

The Workspace features 4 quick-launch buttons for instant evaluation:

1. **1. Single VQA:** Loads Sentinel-2 tile with prompt `"What is visible in this image?"`.
2. **2. Grounding:** Loads urban satellite scene with prompt `"Where are the buildings?"` highlighting cyan bounding boxes.
3. **3. Optical + SAR:** Loads dual-modality pair, tests complementary fusion, and surfaces the cross-sensor disagreement banner.
4. **4. Bi-Temporal Change:** Loads T1 and T2 images with split slider and detects built-up/vegetation change clusters.

---

## 7. Troubleshooting

- **Images not loading preview:** GeoTIFF files are rendered via specialized canvas placeholders to prevent browser memory exhaustion with multi-gigabyte rasters.
- **Backend offline:** The frontend automatically switches to the self-contained mock demo engine if the backend is unreachable.
