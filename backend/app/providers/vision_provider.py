"""
SatQuery AI — Real Vision Provider Stub

This stub raises a clear error when called without configuration.
Replace the body of analyze_image() with real API calls in Phase 8.

Supported providers to implement later:
  - OpenAI GPT-4o Vision
  - Anthropic Claude Vision
  - Google Gemini Vision
  - Azure OpenAI Vision
  - Custom RS-adapted model endpoint
"""

from typing import Any

from app.core.config import get_settings
from app.core.exceptions import ProviderError
from app.providers.base import VisionProvider


class RealVisionProvider(VisionProvider):
    """
    Stub for a real vision API provider.
    Replace body of analyze_image() with actual API call in Phase 8.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def provider_name(self) -> str:
        return self._settings.VISION_PROVIDER

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Phase 8: Replace this body with real API call.
        
        Example for OpenAI GPT-4o:
          response = await openai_client.chat.completions.create(...)
          return parse_response(response)
        """
        raise ProviderError(
            message=(
                f"Real vision provider '{self.provider_name}' is configured but "
                "the implementation is not yet available. "
                "Set DEMO_MODE=true to use mock providers."
            )
        )

    async def health_check(self) -> bool:
        return False
