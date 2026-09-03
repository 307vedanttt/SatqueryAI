# ============================================================
# SatQuery AI — Makefile
# Provides simple commands for development workflow.
# On Windows: use "make" via Git Bash / WSL, or run commands directly.
# ============================================================

.PHONY: help install dev test lint format clean docker-up docker-down validate

# ---- Help ------------------------------------------------
help:
	@echo ""
	@echo "  SatQuery AI — Available Commands"
	@echo ""
	@echo "  make install        Install all dependencies"
	@echo "  make dev            Start backend + frontend in dev mode"
	@echo "  make dev-backend    Start backend only"
	@echo "  make dev-frontend   Start frontend only"
	@echo "  make test           Run all tests"
	@echo "  make lint           Lint backend + frontend"
	@echo "  make format         Format backend + frontend"
	@echo "  make validate       Validate environment"
	@echo "  make docker-up      Start via docker-compose"
	@echo "  make docker-down    Stop docker-compose"
	@echo "  make clean          Remove generated artifacts"
	@echo ""

# ---- Install ---------------------------------------------
install:
	@echo ">>> Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo ">>> Installing frontend dependencies..."
	cd frontend && npm install
	@echo ">>> Creating .env from .env.example (if missing)..."
	@if not exist ".env" (copy .env.example .env && echo ".env created from .env.example") else (echo ".env already exists — skipping")
	@echo ">>> Creating data directories..."
	@if not exist "data\uploads" mkdir data\uploads
	@if not exist "data\results" mkdir data\results
	@if not exist "data\cache" mkdir data\cache
	@echo ">>> Install complete."

# ---- Dev -------------------------------------------------
dev:
	@echo ">>> Starting backend and frontend..."
	@start /B cmd /c "cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
	@start /B cmd /c "cd frontend && npm run dev"
	@echo ">>> Backend: http://localhost:8000"
	@echo ">>> Frontend: http://localhost:5173"
	@echo ">>> API Docs: http://localhost:8000/docs"

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# ---- Test ------------------------------------------------
test:
	@echo ">>> Running backend tests..."
	cd backend && python -m pytest app/tests/ -v --tb=short
	@echo ">>> Running integration tests..."
	cd backend && python -m pytest ../tests/integration/ -v --tb=short

test-backend:
	cd backend && python -m pytest app/tests/ -v --tb=short

test-watch:
	cd backend && python -m pytest app/tests/ -v --tb=short -f

# ---- Lint ------------------------------------------------
lint:
	@echo ">>> Linting backend..."
	cd backend && python -m ruff check app/
	@echo ">>> Linting frontend..."
	cd frontend && npm run lint

# ---- Format ----------------------------------------------
format:
	@echo ">>> Formatting backend..."
	cd backend && python -m ruff format app/
	@echo ">>> Formatting frontend..."
	cd frontend && npm run format

# ---- Validate --------------------------------------------
validate:
	python scripts/validate_environment.py

# ---- Docker ----------------------------------------------
docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# ---- Clean -----------------------------------------------
clean:
	@echo ">>> Cleaning build artifacts..."
	cd frontend && npm run build 2>nul || true
	@if exist "frontend\dist" rmdir /S /Q frontend\dist
	@if exist "backend\__pycache__" rmdir /S /Q backend\__pycache__
	@if exist "backend\.pytest_cache" rmdir /S /Q backend\.pytest_cache
	@echo ">>> Clean complete."
