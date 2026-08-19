"""Runtime wiring for Bitey's governed AI providers."""
import os

from .groq_provider import GroqProvider
from .openrouter_provider import OpenRouterProvider
from .orchestrator import AIOrchestrator
from .registry import AIProviderRegistry, ProviderSpec


def build_ai_orchestrator() -> AIOrchestrator:
    registry = AIProviderRegistry()

    groq = GroqProvider()
    registry.register(
        ProviderSpec(
            name="groq",
            enabled=groq.enabled and os.getenv("GROQ_ENABLED", "true").lower() != "false",
            priority=int(os.getenv("GROQ_PRIORITY", "5")),
            cost_class="free",
            capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"),
            provider=groq,
        )
    )

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
