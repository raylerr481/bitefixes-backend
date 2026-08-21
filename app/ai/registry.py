"""Provider registry for Bitey AI.

Keeps external model providers interchangeable and lets Bitey route tasks
without giving providers authority over business actions.
"""
from dataclasses import dataclass
from typing import Any, Optional

from .free_policy import provider_allowed


@dataclass
class ProviderSpec:
    name: str
    enabled: bool = False
    priority: int = 100
    cost_class: str = "unknown"
    capabilities: tuple[str, ...] = ()
    provider: Any = None


class AIProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ProviderSpec] = {}

    def register(self, spec: ProviderSpec) -> None:
        self._providers[spec.name] = spec

    def available(self, capability: Optional[str] = None) -> list[ProviderSpec]:
        providers = [
            p for p in self._providers.values()
            if p.enabled and p.provider and provider_allowed(p.cost_class)
        ]
        if capability:
            providers = [p for p in providers if capability in p.capabilities]
        return sorted(providers, key=lambda p: (p.priority, p.name))

    def get(self, name: str) -> Optional[ProviderSpec]:
        return self._providers.get(name)

    def snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "name": p.name,
                "enabled": p.enabled and provider_allowed(p.cost_class),
                "priority": p.priority,
                "cost_class": p.cost_class,
                "capabilities": list(p.capabilities),
            }
            for p in sorted(self._providers.values(), key=lambda x: x.name)
        ]
