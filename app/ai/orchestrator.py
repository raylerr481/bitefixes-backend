"""Bitey external-AI orchestrator with health-aware failover."""
from __future__ import annotations
import os
from typing import Any
from .registry import AIProviderRegistry, ProviderSpec
from .provider_health import probe_provider_spec, classify_exception

class AIOrchestrator:
    def __init__(self, registry: AIProviderRegistry) -> None:
        self.registry = registry

    def choose(self, capability: str = "general_reasoning") -> ProviderSpec | None:
        providers = self.registry.available(capability)
        return providers[0] if providers else None

    async def ask(self, prompt: str, *, capability: str = "general_reasoning", context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Use the first healthy provider; automatically fail over on failure."""
        failures = []
        for spec in self.registry.available(capability):
            health = await probe_provider_spec(spec)
            if health is not None and not health.get("ok"):
                failure = {"provider": spec.name, **{k: v for k, v in health.items() if k in ("category", "http_status", "latency_ms", "error_type")}}
                failures.append(failure)
                print(f"[AI ROUTER] provider={spec.name} health=unhealthy category={failure.get('category')} http_status={failure.get('http_status')}")
                continue
            try:
                answer = await spec.provider.generate(prompt, context=context or {})
                if answer:
                    print(f"[AI ROUTER] provider={spec.name} status=selected")
                    return {"status": "ok", "provider": spec.name, "answer": answer, "failures": failures, "health": health}
                failures.append({"provider": spec.name, "category": "empty_response", "http_status": None})
            except Exception as exc:
                diagnostic = classify_exception(exc)
                failures.append({"provider": spec.name, **diagnostic})
                print(f"[AI ROUTER] provider={spec.name} status=error category={diagnostic.get('category')} http_status={diagnostic.get('http_status')}")
        return {"status": "no_provider", "answer": None, "provider": None, "failures": failures}

    async def ask_council(self, prompt: str, *, capability: str = "general_reasoning", context: dict[str, Any] | None = None, max_providers: int | None = None) -> dict[str, Any]:
        """Health-aware bounded council; failed providers never block failover."""
        limit = max_providers or int(os.getenv("AI_COUNCIL_MAX_PROVIDERS", "2"))
        successful, failures = [], []
        for spec in self.registry.available(capability):
            if len(successful) >= max(1, limit):
                break
            health = await probe_provider_spec(spec)
            if health is not None and not health.get("ok"):
                failures.append({"provider": spec.name, **{k: v for k, v in health.items() if k in ("category", "http_status", "latency_ms", "error_type")}})
                print(f"[AI COUNCIL] provider={spec.name} health=unhealthy category={failures[-1].get('category')} http_status={failures[-1].get('http_status')}")
                continue
            try:
                answer = await spec.provider.generate(prompt, context=context or {})
                if answer:
                    successful.append({"provider": spec.name, "answer": answer, "status": "ok", "health": health})
                else:
                    failures.append({"provider": spec.name, "category": "empty_response", "http_status": None})
            except Exception as exc:
                diagnostic = classify_exception(exc)
                failures.append({"provider": spec.name, **diagnostic})
                print(f"[AI COUNCIL] provider={spec.name} status=error category={diagnostic.get('category')} http_status={diagnostic.get('http_status')}")
        if not successful:
            return {"status": "provider_error", "answer": None, "provider": None, "candidates": [], "failures": failures}
        selected = successful[0]
        return {"status": "ok", "provider": selected["provider"], "answer": selected["answer"], "candidates": successful, "failures": failures, "council_used": len(successful) > 1}
