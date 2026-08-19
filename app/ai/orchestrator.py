"""Bitey AI orchestrator.

External models are advisory specialists. Bitey Core remains authoritative
for customer data, knowledge, permissions, workflows and business actions.
"""
from typing import Any

from .registry import AIProviderRegistry, ProviderSpec


class AIOrchestrator:
    def __init__(self, registry: AIProviderRegistry) -> None:
        self.registry = registry

    def choose(self, capability: str = "general_reasoning") -> ProviderSpec | None:
        providers = self.registry.available(capability)
        return providers[0] if providers else None

    async def ask(
        self,
        prompt: str,
        *,
        capability: str = "general_reasoning",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self.choose(capability)
        if not spec:
            return {"status": "no_provider", "answer": None, "provider": None}

        try:
            result = await spec.provider.generate(prompt, context=context or {})
            return {
                "status": "ok",
                "provider": spec.name,
                "answer": result,
            }
        except Exception as exc:
            # Providers are never allowed to break the core conversation path.
            return {
                "status": "provider_error",
                "provider": spec.name,
                "answer": None,
                "error": type(exc).__name__,
            }
