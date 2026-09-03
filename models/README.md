# Model Adapters & Specifications

This directory contains specifications, configuration templates, and adapter interfaces for remote sensing vision-language specialists.

## Directory Structure

- `adapters/`: Specialist adapter wrappers (e.g. VQA, Change Detection, Grounding).
- `configs/`: Model hyperparameters, evaluation configs, and prompt templates.

## Architecture

Specialists inherit from `backend/app/specialists/base.py:Specialist`.

When implementing a genuine remote-sensing adapted model (e.g., fine-tuned VLM or RS specialist):
1. Place adapter code in `adapters/`.
2. Add a `ToolSpec` in `backend/app/registry/registry.py`.
3. Register the implementation with `SpecialistRegistry`.

No router or frontend changes are required.
