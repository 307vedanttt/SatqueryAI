"""
SatQuery AI — Mock Providers

MockVisionProvider and MockLLMProvider return realistic fixture responses.
Used when DEMO_MODE=true or when no real provider is configured.

These providers NEVER call external APIs.
They exist to make the full system runnable without any API keys.
"""

import asyncio
from typing import Any

from app.providers.base import LLMProvider, VisionProvider


class MockVisionProvider(VisionProvider):
    """
    Mock vision provider — returns pre-defined structured responses.
    Simulates a realistic remote-sensing vision model.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Simulate API latency
        await asyncio.sleep(0.10)

        prompt_lower = prompt.lower()

        if "change" in prompt_lower:
            answer = (
                "Significant land-cover changes detected between the two acquisition dates. "
                "Built-up area expansion in the northwest and vegetation loss in the east."
            )
        elif "water" in prompt_lower or "flood" in prompt_lower:
            answer = (
                "A prominent water body occupies the central region. "
                "Spectral signature is consistent with open water. Coverage ~34% of total area."
            )
        elif "built" in prompt_lower or "urban" in prompt_lower:
            answer = (
                "Built-up regions are identifiable in the southwestern quadrant. "
                "High-reflectance surfaces and rectangular structures consistent with settlement."
            )
        elif "sar" in prompt_lower or "radar" in prompt_lower:
            answer = (
                "SAR analysis shows strong double-bounce returns in the northern sector, "
                "indicating dense vertical structures. Smooth specular returns in central water body."
            )
        else:
            answer = (
                "The image shows a heterogeneous landscape with water body, vegetation, "
                "and built-up areas. The terrain is mostly flat with a prominent central water feature."
            )

        return {
            "answer": answer,
            "confidence": 0.82,
            "evidence": [
                {
                    "claim": "Primary land-cover features identified",
                    "bbox": [380, 280, 1150, 880],
                    "confidence": 0.82,
                }
            ],
            "provider": self.provider_name,
            "model": "mock-vision-v1",
        }

    async def health_check(self) -> bool:
        return True


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider — returns structured synthetic responses.
    Used for response synthesis in DEMO_MODE.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        max_tokens: int = 1024,
    ) -> str:
        await asyncio.sleep(0.05)

        # Simple template-based mock generation
        specialist_answer = (context or {}).get("specialist_answer", "")
        if specialist_answer:
            return (
                f"Based on the remote sensing analysis: {specialist_answer} "
                f"This response is synthesized from specialist outputs and available evidence."
            )

        return (
            "The satellite imagery analysis indicates a complex landscape. "
            "The specialist has identified key features with high confidence. "
            "Please refer to the evidence panel for detailed spatial information."
        )

    async def health_check(self) -> bool:
        return True


def get_vision_provider(provider_name: str) -> VisionProvider:
    """Factory — returns the appropriate VisionProvider by name."""
    if provider_name == "mock":
        return MockVisionProvider()
    # Future: elif provider_name == "openai": return OpenAIVisionProvider()
    raise ValueError(f"Unknown vision provider: '{provider_name}'")


def get_llm_provider(provider_name: str) -> LLMProvider:
    """Factory — returns the appropriate LLMProvider by name."""
    if provider_name == "mock":
        return MockLLMProvider()
    # Future: elif provider_name == "openai": return OpenAILLMProvider()
    raise ValueError(f"Unknown LLM provider: '{provider_name}'")
