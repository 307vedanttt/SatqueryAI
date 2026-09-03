"""
agent/ — Agentic Orchestration Core for SatQuery AI

This package implements the BOUNDED, DETERMINISTIC routing and execution brain.
Import order: registry → router → executor → trace

Usage:
    from agent.executor import Executor
    from schemas.contracts import SpecialistRequest, ImageMetadata

    request = SpecialistRequest(query="...", images=[...])
    response, trace = Executor().run(request)
"""
