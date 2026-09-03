"""
SatQuery AI — Abstract Specialist Base

All specialists must implement this interface.
The registry and router interact ONLY with this interface.

Hierarchy:
  Specialist (ABC)
    ├── MockSingleImageSpecialist
    ├── MockOpticalSARSpecialist
    ├── MockChangeDetectionSpecialist
    ├── MockGroundingSpecialist
    └── (future) RSAdaptedSpecialist
              └── (future) APIVisionSpecialist
"""

from abc import ABC, abstractmethod

from app.models.schemas import SpecialistRequest, SpecialistResult


class Specialist(ABC):
    """Abstract base for all specialists."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name matching the registry ToolSpec name."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """List of capability strings this specialist provides."""
        ...

    @abstractmethod
    async def execute(self, request: SpecialistRequest) -> SpecialistResult:
        """
        Execute analysis for the given request.
        
        Args:
            request: Fully typed SpecialistRequest including file paths,
                     metadata, query, and parameters.
        
        Returns:
            SpecialistResult with answer, evidence, and confidence.
        
        Must NOT:
          - Execute arbitrary shell commands
          - Access arbitrary files outside request.file_paths
          - Call unregistered external services
          - Silently swallow errors
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
