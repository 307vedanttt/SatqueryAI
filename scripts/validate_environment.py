"""
SatQuery AI — Environment & System Validation Script

Verifies:
  - Python version (3.10+)
  - FastApi, Pydantic v2, SQLAlchemy
  - rasterio / GDAL availability
  - Environment variables
  - Storage directories
  - Database connectivity

Run this script to confirm your system is ready.
Never prints secrets or API keys.
"""

import os
import sys
from pathlib import Path


def check_python_version() -> bool:
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 10
    status = "✓" if ok else "✗"
    print(f"{status} Python {v.major}.{v.minor}.{v.micro} (required: 3.10+)")
    return ok


def check_backend_deps() -> bool:
    all_ok = True
    deps = ["fastapi", "uvicorn", "pydantic", "sqlalchemy", "pydantic_settings"]
    for d in deps:
        try:
            __import__(d)
            print(f"✓ {d}")
        except ImportError:
            print(f"✗ {d} (missing)")
            all_ok = False
    return all_ok


def check_rasterio() -> bool:
    try:
        import rasterio
        print(f"✓ rasterio {rasterio.__version__} (GeoTIFF supported)")
        return True
    except ImportError:
        print("! rasterio not found — GeoTIFF metadata extraction limited (using fallback)")
        return False


def check_env_vars() -> bool:
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file exists")
    else:
        print("! .env file missing — copy .env.example to .env")

    from app.core.config import get_settings
    settings = get_settings()
    print(f"✓ APP_ENV: {settings.APP_ENV}")
    print(f"✓ DEMO_MODE: {settings.DEMO_MODE}")
    print(f"✓ LLM_PROVIDER: {settings.effective_llm_provider}")
    print(f"✓ VISION_PROVIDER: {settings.effective_vision_provider}")
    return True


def check_directories() -> bool:
    dirs = ["./data/uploads", "./data/results", "./data/cache"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"✓ Directory ready: {d}")
    return True


def check_db() -> bool:
    try:
        from app.models.database import check_db_connection, init_db
        init_db()
        if check_db_connection():
            print("✓ Database connection successful")
            return True
        else:
            print("✗ Database connection failed")
            return False
    except Exception as e:
        print(f"✗ Database check error: {e}")
        return False


def main():
    print("==================================================")
    print("SatQuery AI — Environment Validation")
    print("==================================================")

    # Add backend to path
    backend_path = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_path.resolve()))

    results = [
        check_python_version(),
        check_backend_deps(),
        check_rasterio(),
        check_env_vars(),
        check_directories(),
        check_db(),
    ]

    print("==================================================")
    if all(results):
        print("✓ Environment ready. Run 'make dev' to start.")
    else:
        print("! Environment checks complete with warnings.")
    print("==================================================")


if __name__ == "__main__":
    main()
