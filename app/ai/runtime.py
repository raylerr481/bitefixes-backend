"""Runtime wiring for Bitey's governed AI providers.

The registry is intentionally free/local-first. External providers remain
optional advisors and can never become the source of truth for tenant data or
business actions.
"""
import os

from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .ollama_provider import OllamaProvider
from .openrouter_provider import OpenRouterProvider
from .orchestrator import AIOrchestrator
from .registry import AIProviderRegistry, ProviderSpec


CAPABILITIES = ("general_reasoning", "semantic_analysis", "language", "extraction")


def _priority(name: str, default: int) -> int:
    try:
        return int(os.getenv(f"{name.upper()}_PRIORITY", str(default)))
    except ValueError:
        return default


def build_ai_orchestrator() -> AIOrchestrator:
    registry = AIProviderRegistry()

    ollama = OllamaProvider()
    registry.register(ProviderSpec(
        name="ollama-local",
        enabled=ollama.enabled,
        priority=_priority("ollama", 1),
        cost_class="local-free",
        capabilities=CAPABILITIES,
        provider=ollama,
    ))

    groq = GroqProvider()
    registry.register(ProviderSpec(
        name="groq",
        enabled=groq.enabled and os.getenv("GROQ_ENABLED", "true").lower() != "false",
        priority=_priority("groq", 5),
        cost_class="free-tier",
        capabilities=CAPABILITIES,
        provider=groq,
    ))

    openrouter = OpenRouterProvider()
    registry.register(ProviderSpec(
        name="openrouter-free",
        enabled=openrouter.enabled and os.getenv("OPENROUTER_ENABLED", "true").lower() != "false",
        priority=_priority("openrouter", 10),
        cost_class="free-tier",
        capabilities=CAPABILITIES,
        provider=openrouter,
    ))

    gemini = GeminiProvider()
    registry.register(ProviderSpec(
        name="gemini",
        enabled=gemini.enabled,
        priority=_priority("gemini", 20),
        cost_class="free-tier",
        capabilities=CAPABILITIES,
        provider=gemini,
    ))

    return AIOrchestrator(registry)
