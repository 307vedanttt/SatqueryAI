# SatQuery AI — Reproducibility Checklist & Pre-Presentation Guide

## 1. Environment Setup Checklist

- [ ] Python 3.10+ installed
- [ ] Dependencies installed via `make install` or `pip install -r backend/requirements.txt`
- [ ] PyTorch & torchvision installed (GPU/CUDA verified if available: `python -c "import torch; print(torch.cuda.is_available())"`)
- [ ] Environment validated via `python scripts/validate_environment.py`

## 2. Model Downloads & Caching

- Qwen2.5-VL-3B-Instruct model weights cached on first run (`Qwen/Qwen2.5-VL-3B-Instruct`).
- Fallback CPU float32 mode active if no CUDA GPU present.

## 3. Launching the Demo

### Option A: Gradio Demo UI (Primary Presentation)
```bash
python frontend/app.py
```
Access at http://localhost:7860

### Option B: FastAPI Backend + React UI
```bash
make dev
```
- API Docs: http://localhost:8000/docs
- React UI: http://localhost:5173

## 4. Pre-Presentation Checklist

- [ ] Sample single optical GeoTIFF ready
- [ ] Sample Optical + SAR pair ready
- [ ] Sample bi-temporal image pair ready
- [ ] Pre-selected queries tested on Gradio UI
- [ ] `python scripts/manual_test_agent.py` executed successfully
- [ ] `python evaluation/run_eval.py` executed successfully
