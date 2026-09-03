# SatQuery AI — Routing & Orchestration Documentation

## Input Configuration Classification
- `SINGLE_OPTICAL`: One optical or multispectral image.
- `SINGLE_SAR`: One SAR image.
- `OPTICAL_SAR_PAIR`: One optical and one SAR image.
- `BI_TEMPORAL`: Two images of the same area taken at different dates.

## Query Intent Taxonomy
- `SCENE_DESCRIPTION`
- `VQA`
- `GROUNDING`
- `CHANGE_DESCRIPTION`
- `CHANGE_VQA`
- `OPTICAL_SAR_ANALYSIS`
- `BUILT_UP_ANALYSIS`
- `WATER_ANALYSIS`
- `OBJECT_IDENTIFICATION`

## Execution Graph
The router selects a specialist registered in `SpecialistRegistry` based on the deterministic `ROUTING_TABLE`.
