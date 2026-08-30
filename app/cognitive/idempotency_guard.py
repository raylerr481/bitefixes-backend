"""Domain-agnostic message idempotency guard for Bitey's processing pipeline."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional


def message_fingerprint(message: str, *, conversation_id: Optional[str] = None, sender: Optional[str] = None) -> str:
    raw = "|".join((str(conversation_id or ""), str(sender or ""), (message or "").strip()))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class IdempotencyGuard:
    """Small process-local guard; persistent adapters can implement the same contract."""

    def __init__(self) -> None:
        self._processed: Dict[str, Any] = {}

    def get(self, key: str) -> Any:
        return self._processed.get(key)

    def mark(self, key: str, result: Any) -> Any:
        if key in self._processed:
            return self._processed[key]
        self._processed[key] = result
        return result

    def process(self, key: str, handler) -> Any:
        existing = self.get(key)
        if existing is not None:
            return existing
        return self.mark(key, handler())
