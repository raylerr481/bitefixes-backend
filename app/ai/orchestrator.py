"""Bitey AI provider orchestration.

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
        providers = self.registry.available(capability)
        if not providers:
            return {"status": "no_provider", "answer": None, "provider": None}

        errors: list[str] = []
        for spec in providers:
            try:
                result = await spec.provider.generate(prompt, context=context or {})
                if result:
                    return {"status": "ok", "provider": spec.name, "answer": result}
                errors.append(f"{spec.name}:empty_response")
            except Exception as exc:
                errors.append(f"{spec.name}:{type(exc).__name__}")

        return {"status": "provider_error", "provider": None, "answer": None, "errors": errors}


def build_default_orchestrator() -> AIOrchestrator:
    from .providers import build_provider_registry
    return AIOrchestrator(build_provider_registry())
