"""
SatQuery AI — Abstract Provider Interfaces

These ABC interfaces decouple all business logic from specific AI providers.
The rest of the application interacts ONLY with these interfaces.

Architecture:
  VisionProvider → MockVisionProvider | RealVisionProvider
  LLMProvider    → MockLLMProvider    | RealLLMProvider
"""

from abc import ABC, abstractmethod
from typing import Any


class VisionProvider(ABC):
    """
    Interface for vision/image understanding providers.
    
    Implementations must be swappable without changing
    the router, specialists, or evidence layer.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""
        ...

    @abstractmethod
    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze a single image with a text prompt.
        
        Args:
            image_path: Absolute path to the image file.
            prompt: Natural language analysis instruction.
            metadata: Optional image metadata hints.
        
        Returns:
            Dict with at minimum:
              - "answer": str
              - "confidence": float
              - "evidence": list[dict]
        
        Must NOT:
          - Read files outside image_path
          - Execute shell commands
          - Return raw API error messages to callers
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable and functional."""
        ...


class LLMProvider(ABC):
    """
    Interface for language model providers used for
    response synthesis and intent refinement.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        max_tokens: int = 1024,
    ) -> str:
        """
        Generate a text response given a prompt and optional context.
        
        Args:
            prompt: The generation prompt.
            context: Optional structured context dict.
            max_tokens: Maximum response length.
        
        Returns:
            Generated text string.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
