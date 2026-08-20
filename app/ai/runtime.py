"""Single runtime entrypoint for Bitey's governed AI stack.

The default runtime uses the unified provider registry from ``providers.py``.
Bitey Core remains authoritative; external models are advisory specialists.
"""
from .orchestrator import AIOrchestrator


def build_ai_orchestrator() -> AIOrchestrator:
    """Build the canonical Bitey provider router.

    Providers are enabled only when configured. The registry itself remains
    usable without cloud credentials, so local/core functionality is preserved.
    """
    from .providers import build_provider_registry

    return AIOrchestrator(build_provider_registry())
