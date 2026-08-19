"""Runtime wiring for Bitey's governed AI providers."""
import os

from .orchestrator import AIOrchestrator
from .openrouter_provider import OpenRouterProvider
from .registry import AIProviderRegistry, ProviderSpec


def build_ai_orchestrator() -> AIOrchestrator:
    registry = AIProviderRegistry()
    openrouter = OpenRouterProvider()
    registry.register(
        ProviderSpec(
            name="openrouter-free",
            enabled=openrouter.enabled,
            priority=int(os.getenv("OPENROUTER_PRIORITY", "10")),
            cost_class="free",
            capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"),
            provider=openrouter,
        )
    )
    return AIOrchestrator(registry)
