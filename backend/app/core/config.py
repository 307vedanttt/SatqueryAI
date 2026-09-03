"""
SatQuery AI — Application Configuration

Loads all settings from environment variables using Pydantic Settings.
API keys are NEVER logged, printed, or exposed.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "SatQuery AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # --- Demo / Mock ---
    DEMO_MODE: bool = True
    ALLOW_MOCK_FALLBACK: bool = False

    # --- Security ---
    MAX_UPLOAD_SIZE_MB: int = 50

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./data/satquery.db"

    # --- Storage ---
    STORAGE_PATH: str = "./data"
    UPLOAD_DIR: str = "./data/uploads"
    RESULTS_DIR: str = "./data/results"
    CACHE_DIR: str = "./data/cache"

    # --- LLM Provider ---
    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = Field(default="", repr=False)  # repr=False → never printed
    LLM_MODEL: str = ""
    LLM_BASE_URL: str = ""
    LLM_TIMEOUT_SECONDS: int = 30

    # --- Vision Provider ---
    VISION_PROVIDER: str = "mock"
    VISION_API_KEY: str = Field(default="", repr=False)
    VISION_MODEL: str = ""
    VISION_BASE_URL: str = ""
    VISION_TIMEOUT_SECONDS: int = 60

    # --- Confidence Thresholds ---
    CONFIDENCE_THRESHOLD_LOW: float = 0.40
    CONFIDENCE_THRESHOLD_HIGH: float = 0.75

    # Confidence component weights — must sum to 1.0
    CONFIDENCE_WEIGHT_INPUT: float = 0.20
    CONFIDENCE_WEIGHT_SPECIALIST: float = 0.40
    CONFIDENCE_WEIGHT_EVIDENCE: float = 0.20
    CONFIDENCE_WEIGHT_AGREEMENT: float = 0.20

    # --- CORS ---
    FRONTEND_URL: str = "http://localhost:5173"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @field_validator("CONFIDENCE_WEIGHT_INPUT", "CONFIDENCE_WEIGHT_SPECIALIST",
                     "CONFIDENCE_WEIGHT_EVIDENCE", "CONFIDENCE_WEIGHT_AGREEMENT",
                     mode="before")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        if not (0.0 <= float(v) <= 1.0):
            raise ValueError("Confidence weight must be between 0.0 and 1.0")
        return float(v)

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def effective_llm_provider(self) -> str:
        return self.LLM_PROVIDER if not self.DEMO_MODE else "mock"

    @property
    def effective_vision_provider(self) -> str:
        return self.VISION_PROVIDER if not self.DEMO_MODE else "mock"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance. Call this everywhere instead of instantiating directly."""
    return Settings()
