"""Bitey external-AI orchestrator with health-aware, incremental failover."""
from __future__ import annotations
import os
from typing import Any
from .registry import AIProviderRegistry, ProviderSpec
from .provider_health import probe_provider_spec, classify_exception
from .incremental_registry import IncrementalProviderStore, ProviderObservation

class AIOrchestrator:
    def __init__(self, registry: AIProviderRegistry, observation_store: IncrementalProviderStore | None = None) -> None:
        self.registry = registry
        self.observation_store = observation_store or IncrementalProviderStore()

    def choose(self, capability: str = "general_reasoning") -> ProviderSpec | None:
        providers = self.registry.available(capability)
        return providers[0] if providers else None

    def _record(self, spec: ProviderSpec, health: dict[str, Any] | None, status: str, category: str | None = None, http_status: int | None = None) -> None:
        provider = getattr(spec, "provider", None)
        model = str(getattr(provider, "model", "unknown"))
        caps = tuple(getattr(spec, "capabilities", ()) or ())
        self.observation_store.upsert_observation(ProviderObservation(spec.name, model, caps, status=status, http_status=http_status if http_status is not None else (health or {}).get("http_status"), category=category or (health or {}).get("category"), latency_ms=(health or {}).get("latency_ms")))

    async def ask(self, prompt: str, *, capability: str = "general_reasoning", context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Try providers incrementally; preserve every candidate and diagnostic."""
        failures = []
        for spec in self.registry.available(capability):
            health = await probe_provider_spec(spec)
            if health is not None and not health.get("ok"):
                failure = {"provider": spec.name, **{k: v for k, v in health.items() if k in ("category", "http_status", "latency_ms", "error_type")}}
                failures.append(failure); self._record(spec, health, "unhealthy")
                print(f"[AI ROUTER] provider={spec.name} health=unhealthy category={failure.get('category')} http_status={failure.get('http_status')}")
                continue
            try:
                answer = await spec.provider.generate(prompt, context=context or {})
                if answer:
                    self._record(spec, health, "healthy")
                    print(f"[AI ROUTER] provider={spec.name} status=selected")
                    return {"status": "ok", "provider": spec.name, "answer": answer, "failures": failures, "health": health, "provider_observations": self.observation_store.snapshot()}
                failures.append({"provider": spec.name, "category": "empty_response", "http_status": None}); self._record(spec, health, "degraded", "empty_response")
            except Exception as exc:
                diagnostic = classify_exception(exc); failures.append({"provider": spec.name, **diagnostic}); self._record(spec, health, "failed", diagnostic.get("category"), diagnostic.get("http_status"))
                print(f"[AI ROUTER] provider={spec.name} status=error category={diagnostic.get('category')} http_status={diagnostic.get('http_status')}")
        return {"status": "no_provider", "answer": None, "provider": None, "failures": failures, "provider_observations": self.observation_store.snapshot()}

    async def ask_council(self, prompt: str, *, capability: str = "general_reasoning", context: dict[str, Any] | None = None, max_providers: int | None = None) -> dict[str, Any]:
        """Health-aware bounded council; failed providers never block failover."""
        limit = max_providers or int(os.getenv("AI_COUNCIL_MAX_PROVIDERS", "2")); successful, failures = [], []
        for spec in self.registry.available(capability):
            if len(successful) >= max(1, limit): break
            health = await probe_provider_spec(spec)
            if health is not None and not health.get("ok"):
                failures.append({"provider": spec.name, **{k: v for k, v in health.items() if k in ("category", "http_status", "latency_ms", "error_type")}}); self._record(spec, health, "unhealthy"); continue
            try:
                answer = await spec.provider.generate(prompt, context=context or {})
                if answer:
                    successful.append({"provider": spec.name, "answer": answer, "status": "ok", "health": health}); self._record(spec, health, "healthy")
                else:
                    failures.append({"provider": spec.name, "category": "empty_response", "http_status": None}); self._record(spec, health, "degraded", "empty_response")
            except Exception as exc:
                diagnostic = classify_exception(exc); failures.append({"provider": spec.name, **diagnostic}); self._record(spec, health, "failed", diagnostic.get("category"), diagnostic.get("http_status"))
        if not successful: return {"status": "provider_error", "answer": None, "provider": None, "candidates": [], "failures": failures, "provider_observations": self.observation_store.snapshot()}
        selected = successful[0]
        return {"status": "ok", "provider": selected["provider"], "answer": selected["answer"], "candidates": successful, "failures": failures, "council_used": len(successful) > 1, "provider_observations": self.observation_store.snapshot()}
