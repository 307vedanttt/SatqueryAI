# SatQuery AI — Reproducibility & Demo Checklist

## Environment Setup
- [ ] Python 3.11+ installed (Recommended: conda or venv)
- [ ] `pip install -r requirements.txt` (from repo root)
- [ ] (Optional) GPU with CUDA for fast inference
- [ ] Verify PyTorch installation with CUDA support (if available)
- [ ] Check rasterio and GDAL installations (often tricky on Windows/Mac, consider conda if issues arise)

## Model Downloads
- [ ] Qwen2.5-VL-3B-Instruct (~6GB): will auto-download on first run of models/vqa/
- [ ] Download custom pre-trained checkpoints (if any) and place them in `models/weights/`
- [ ] Ensure enough disk space (~20GB recommended) for model caching

## Data Preparation
- [ ] Populate `data/` directory with sample images corresponding to evaluation sets
- [ ] Run `python -m evaluation.run_eval` to ensure the pipeline runs without fatal errors
- [ ] Verify test image paths in `evaluation/test_set.py`

## Running the Backend
- [ ] Start the FastAPI backend server from repo root: `uvicorn backend.main:app --reload`
- [ ] Verify the API is up at `http://localhost:8000/docs`
- [ ] Check logs for any initialization errors from model loaders

## Running the Frontend
- [ ] Install dependencies (e.g., `pip install gradio`)
- [ ] Start the frontend interface from repo root: `python frontend/app.py`
- [ ] By default, the Gradio demo calls the Executor directly to minimize moving parts. To use the HTTP API instead, update the analyze function in `app.py` to use `requests.post` to `http://localhost:8000/query`.

## Pre-Presentation Checklist
- [ ] Sample images loaded and tested via the UI
- [ ] Demo queries pre-typed and tested (warm-up models to avoid first-run latency)
- [ ] Screen recording backup available (in case of live demo failure)
- [ ] Backup laptop/tablet ready with a pre-recorded demo video
- [ ] Clear cache if demonstrating fresh runs

## Troubleshooting
- **Out of Memory (OOM):** Ensure GPU has at least 8GB VRAM for the 3B model. Use CPU fallback or quantization if needed.
- **Model downloading slowly:** Pre-download weights manually using `huggingface-cli download`.
- **Rasterio errors:** Verify GDAL paths. `conda install -c conda-forge rasterio` is highly recommended.
