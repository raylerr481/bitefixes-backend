"""Bitey external-AI orchestrator with transport health and incremental failover.

Bitey never compares, scores, rewrites, or selects between cognitive answers.
One external provider owns each cognitive turn; another provider is used only
when the current provider fails operationally.
"""
from __future__ import annotations

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
        h = health or {}
        self.observation_store.upsert_observation(
            ProviderObservation(
                spec.name,
                model,
                caps,
                status=status,
                http_status=http_status if http_status is not None else h.get("http_status"),
                category=category or h.get("category"),
                latency_ms=h.get("latency_ms"),
            )
        )

    async def ask(self, prompt: str, *, capability: str = "general_reasoning", context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Give one external AI the cognitive turn; fail over only on operational failure."""
        failures: list[dict[str, Any]] = []
        for spec in self.registry.available(capability):
            health = await probe_provider_spec(spec)
            if health is not None and not health.get("ok"):
                diagnostic = {"provider": spec.name, **{k: v for k, v in health.items() if k in ("category", "http_status", "latency_ms", "error_type")}}
                failures.append(diagnostic)
                self._record(spec, health, "unhealthy")
                print(f"[AI ROUTER] provider={spec.name} health=unhealthy category={diagnostic.get('category')} http_status={diagnostic.get('http_status')}")
                continue
            try:
                answer = await spec.provider.generate(prompt, context=context or {})
                if answer and answer.strip():
                    self._record(spec, health, "healthy", "selected")
                    print(f"[AI ROUTER] provider={spec.name} status=selected")
                    return {
                        "status": "ok",
                        "provider": spec.name,
                        "answer": answer.strip(),
                        "failures": failures,
                        "health": health,
                        "provider_observations": self.observation_store.snapshot(),
                    }
                diagnostic = {"provider": spec.name, "category": "empty_response", "http_status": health.get("http_status") if health else None}
                failures.append(diagnostic)
                self._record(spec, health, "degraded", "empty_response")
                print(f"[AI ROUTER] provider={spec.name} status=empty_response")
            except Exception as exc:
                diagnostic = {"provider": spec.name, **classify_exception(exc)}
                failures.append(diagnostic)
                self._record(spec, health, "failed", diagnostic.get("category"), diagnostic.get("http_status"))
                print(f"[AI ROUTER] provider={spec.name} status=error category={diagnostic.get('category')} http_status={diagnostic.get('http_status')}")
        return {"status": "no_provider", "answer": None, "provider": None, "failures": failures, "provider_observations": self.observation_store.snapshot()}

    async def ask_council(self, prompt: str, *, capability: str = "general_reasoning", context: dict[str, Any] | None = None, max_providers: int | None = None) -> dict[str, Any]:
        """Compatibility alias: a council request is still one-provider cognition.

        The legacy name remains to avoid breaking callers, but it never queries
        multiple successful models, compares answers, or performs cognitive
        arbitration. ``max_providers`` is intentionally ignored.
        """
        return await self.ask(prompt, capability=capability, context=context)
