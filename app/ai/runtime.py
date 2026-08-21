"""Runtime wiring for Bitey's governed cognitive council."""
import os

from .groq_provider import GroqProvider
from .openrouter_provider import OpenRouterProvider, QWEN_FREE_MODEL, DEEPSEEK_FREE_MODEL
from .orchestrator import AIOrchestrator
from .registry import AIProviderRegistry, ProviderSpec


def build_ai_orchestrator() -> AIOrchestrator:
    registry = AIProviderRegistry()

    groq = GroqProvider()
    registry.register(ProviderSpec(
        name="groq",
        enabled=groq.enabled and os.getenv("GROQ_ENABLED", "true").lower() != "false",
        priority=int(os.getenv("GROQ_PRIORITY", "5")),
        cost_class="free",
        capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"),
        provider=groq,
    ))

    qwen = OpenRouterProvider(model=os.getenv("OPENROUTER_QWEN_MODEL", QWEN_FREE_MODEL))
    registry.register(ProviderSpec(
        name="qwen-free",
        enabled=qwen.enabled,
        priority=int(os.getenv("QWEN_PRIORITY", "10")),
        cost_class="free",
        capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"),
        provider=qwen,
    ))

    deepseek = OpenRouterProvider(model=os.getenv("OPENROUTER_DEEPSEEK_MODEL", DEEPSEEK_FREE_MODEL))
    registry.register(ProviderSpec(
        name="deepseek-free",
        enabled=deepseek.enabled and os.getenv("DEEPSEEK_ENABLED", "true").lower() != "false",
        priority=int(os.getenv("DEEPSEEK_PRIORITY", "15")),
        cost_class="free",
        capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"),
        provider=deepseek,
    ))

    return AIOrchestrator(registry)
