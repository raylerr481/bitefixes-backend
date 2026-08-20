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
                error_code = "empty_response"
                errors.append(f"{spec.name}:{error_code}")
                self._record_provider_incident(spec, error_code, capability)
            except Exception as exc:
                error_code = type(exc).__name__
                errors.append(f"{spec.name}:{error_code}")
                self._record_provider_incident(spec, error_code, capability)

        return {"status": "provider_error", "provider": None, "answer": None, "errors": errors}

    @staticmethod
    def _record_provider_incident(spec: ProviderSpec, error_code: str, capability: str) -> None:
        """Best-effort incident capture; observability must never break fallback."""
        try:
            from app.services.incident_service import record_incident
            record_incident(
                message=f"AI provider failure: {error_code}",
                severity="warning",
                component="ai_orchestrator",
                error_code=error_code,
                error_type="provider_failure",
                provider=spec.name,
                operation="generate",
                context={"capability": capability},
            )
        except Exception:
            pass


def build_default_orchestrator() -> AIOrchestrator:
    from .providers import build_provider_registry
    return AIOrchestrator(build_provider_registry())
