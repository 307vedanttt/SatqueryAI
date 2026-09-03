# SatQuery AI — Vision-Language Assistant for Remote Sensing

**Problem Statement SIH26167 — ISRO Department of Space — SIH 2026**

SatQuery AI is an interactive vision-language assistant for multimodal remote sensing image analysis through text queries.

> **"Don't choose the model. Ask the question."**

---

## Features

- **Automated Configuration Classification**: Automatically detects `SINGLE_OPTICAL`, `SINGLE_SAR`, `OPTICAL_SAR_PAIR`, and `BI_TEMPORAL` inputs.
- **GeoTIFF Ingestion**: Extracts CRS, spatial resolution, bounding box, bands, and sensor tags using `rasterio`.
- **Pair Alignment Validation**: Validates spatial alignment, CRS compatibility, and resolution tolerance prior to analysis.
- **Bounded Orchestration**: Bounded execution graph mapping intent to registered specialist tools.
- **Evidence & Confidence**: Multi-factor confidence scoring with explicit disagreement detection across sensors.
- **Execution Trace**: Step-by-step auditability exposing execution timing, components, and status.
- **API-First & Swappable Providers**: Abstract `VisionProvider` and `LLMProvider` interfaces supporting full `DEMO_MODE`.

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy, rasterio
- **Frontend**: React 18, TypeScript, Vite, Vanilla CSS
- **Testing**: pytest, pytest-asyncio, httpx

---

## Getting Started

```bash
# Clone the repository
git clone https://github.com/307vedanttt/SatqueryAI.git
cd SatqueryAI

# Copy environment template
cp .env.example .env

# Validate environment setup
python scripts/validate_environment.py

# Run development servers
make dev
```

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend UI: http://localhost:5173

---

## Monorepo Architecture

```text
satquery-ai/
├── backend/            # FastAPI Backend & Orchestrator
│   ├── app/
│   │   ├── api/        # REST API Routes (/upload, /analyze, /health)
│   │   ├── core/       # Settings, Logging, Security, Exceptions
│   │   ├── ingestion/  # GeoTIFF raster extraction & Pair alignment
│   │   ├── router/     # Configuration & Intent classification, Execution graph
│   │   ├── registry/   # Specialist & Tool registry
│   │   ├── specialists/# Single image, Optical-SAR, Change detection, Grounding
│   │   ├── providers/  # Provider abstractions & Mock providers
│   │   ├── evidence/   # Synthesizer, Confidence calculator, Disagreement detector
│   │   └── trace/      # Execution trace recorder & formatter
├── frontend/           # React + TypeScript + Vite UI
├── docs/               # Architecture, Routing, API, Security documentation
├── scripts/            # Environment validation & Demo seeding scripts
└── tests/              # End-to-end integration test suite
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
