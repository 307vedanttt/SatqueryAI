# SatQuery AI — Architecture Documentation

## System Architecture

```text
                    ┌──────────────────────┐
                    │      FRONTEND        │
                    │   React + Vite UI    │
                    └──────────┬───────────┘
                               │ HTTP / JSON
                               ▼
                    ┌──────────────────────┐
                    │       FASTAPI        │
                    │      BACKEND         │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      ┌────────────┐    ┌─────────────┐   ┌──────────────┐
      │ Ingestion  │    │   Router    │   │  Session /   │
      │ Validation │    │ Orchestrator│   │ Metadata DB  │
      └────────────┘    └──────┬──────┘   └──────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    MODEL / TOOL      │
                    │       REGISTRY       │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      ┌─────────────┐   ┌──────────────┐  ┌──────────────┐
      │ Single Img  │   │ Optical-SAR  │  │ Bi-temporal  │
      │ Specialist  │   │ Specialist   │  │ Specialist   │
      └─────────────┘   └──────────────┘  └──────────────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ EVIDENCE SYNTHESIS   │
                    │ + CONFIDENCE         │
                    │ + DISAGREEMENT       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ EXECUTION TRACE      │
                    │ + FINAL RESPONSE     │
                    └──────────┬───────────┘
```

## Key Architectural Principles

1. **API-First & Swappable Providers**: Abstract interfaces (`VisionProvider`, `LLMProvider`) ensure business logic is decoupled from external APIs.
2. **Deterministic Bounded Orchestration**: The router maps (InputConfig, Intent) to registered specialists. Free-form, unbounded agent loops are strictly prohibited.
3. **Evidence-Backed Answers & Fail-Safe Refusal**: Confidence is computed using a weighted formula. If confidence falls below the low threshold, the system refuses to guess.
4. **GeoTIFF Verification**: Spatial alignment, CRS, and resolution tolerances are strictly enforced prior to multimodal or bi-temporal processing.
