"""
SatQuery AI — Backend Application Entry Point

FastAPI application factory with:
- Lifespan management (DB init, registry bootstrap)
- CORS configuration
- API router mounting
- Global exception handlers
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analysis, health, sessions, upload
from app.core.config import get_settings
from app.core.exceptions import SatQueryError
from app.core.logging import get_logger
from app.models.database import init_db
from app.registry.registry import SpecialistRegistry

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown logic."""
    # Startup
    logger.info("satquery_startup", version=settings.APP_VERSION, demo_mode=settings.DEMO_MODE)
    init_db()
    registry: SpecialistRegistry = app.state.registry
    registry.bootstrap()
    logger.info("registry_bootstrapped", tool_count=len(registry.list_tools()))
    yield
    # Shutdown
    logger.info("satquery_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="SatQuery AI",
        description=(
            "Interactive Vision-Language Assistant for Multimodal "
            "Remote Sensing Image Analysis — SIH 2026 / ISRO"
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Ensure database schema is initialized
    init_db()

    # Attach registry to app state so routes can access it
    app.state.registry = SpecialistRegistry()
    app.state.registry.bootstrap()

    # CORS — allow frontend origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global SatQuery error handler — never exposes stack traces
    @app.exception_handler(SatQueryError)
    async def satquery_error_handler(request: Request, exc: SatQueryError) -> JSONResponse:
        logger.error(
            "satquery_error",
            error_code=exc.error_code,
            message=exc.message,
            path=str(request.url),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.error_code, "message": exc.message, "details": exc.details}},
        )

    # Catch-all for unhandled exceptions — log details server-side, return safe response
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", path=str(request.url), exc_type=type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again.",
                    "details": {},
                }
            },
        )

    # Mount routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])
    app.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])

    return app


app = create_app()
