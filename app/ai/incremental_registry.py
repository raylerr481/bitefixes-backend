"""Incremental provider registry persistence contract.

This layer intentionally never replaces providers. It merges observations by
(provider, model) identity and keeps failed/degraded candidates for retry.
Secrets are never stored here.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class ProviderObservation:
    provider: str
    model: str
    capabilities: tuple[str, ...] = ()
    status: str = "unknown"
    http_status: int | None = None
    category: str | None = None
    latency_ms: float | None = None
    quality_score: float | None = None
    attempts: int = 0
    last_checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class IncrementalProviderStore:
    """In-memory contract used by the orchestrator; persistence can be backed by Supabase."""
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], ProviderObservation] = {}

    def upsert_observation(self, observation: ProviderObservation) -> ProviderObservation:
        key = (observation.provider, observation.model)
        previous = self._items.get(key)
        if previous:
            observation.attempts = previous.attempts + 1
            if not observation.capabilities:
                observation.capabilities = previous.capabilities
        self._items[key] = observation
        return observation

    def candidates(self) -> list[ProviderObservation]:
        return list(self._items.values())

    def snapshot(self) -> list[dict[str, Any]]:
        return [o.__dict__.copy() for o in self._items.values()]
