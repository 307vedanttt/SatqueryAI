# SatQuery AI — Model & Specialist Registry

## Registering a Specialist

1. Implement `backend/app/specialists/base.py:Specialist`.
2. Define a `ToolSpec` (name, capabilities, supported inputs/intents).
3. Register via `registry.register(spec, implementation)` in `backend/app/registry/registry.py`.

## Swapping Mock with Real AI
Set `DEMO_MODE=false` and configure `VISION_PROVIDER` / `LLM_PROVIDER` in `.env`.
