"""
SatQuery AI — Registry Schemas

ToolSpec defines the complete contract for a registered specialist/tool.
Only tools present in the registry can be executed.
"""

from pydantic import BaseModel, Field


class ToolSpec(BaseModel):
    """Full specification for a registered specialist tool."""

    name: str = Field(description="Unique tool identifier")
    version: str = Field(description="Semantic version string")
    display_name: str = Field(description="Human-readable name")
    description: str = Field(description="What this tool does")
    capabilities: list[str] = Field(description="Capability tags this tool satisfies")
    supported_input_configurations: list[str] = Field(
        description="InputConfiguration values this tool accepts"
    )
    supported_intents: list[str] = Field(
        description="QueryIntent values this tool can handle"
    )
    required_parameters: list[str] = Field(default_factory=list)
    provider: str = Field(description="Provider name: 'mock' | 'openai' | etc.")
    timeout_seconds: int = Field(default=60)
    enabled: bool = Field(default=True)
    metadata: dict = Field(default_factory=dict)
