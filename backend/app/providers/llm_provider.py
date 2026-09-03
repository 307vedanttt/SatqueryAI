"""
SatQuery AI — Real LLM Provider Stub

Stub for real LLM API integration. Replace in Phase 8.
"""

from typing import Any

from app.core.config import get_settings
from app.core.exceptions import ProviderError
from app.providers.base import LLMProvider


class RealLLMProvider(LLMProvider):
    """Stub for real LLM provider. Implement in Phase 8."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def provider_name(self) -> str:
        return self._settings.LLM_PROVIDER

    async def generate(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        max_tokens: int = 1024,
    ) -> str:
        raise ProviderError(
            message=(
                f"Real LLM provider '{self.provider_name}' is configured but "
                "the implementation is not yet available. "
                "Set DEMO_MODE=true to use mock providers."
            )
        )

    async def health_check(self) -> bool:
        return False
