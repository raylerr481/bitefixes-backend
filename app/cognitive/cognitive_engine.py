"""Bitey Cognitive Engine.

Combines:
- OpenCog Hyperon/MeTTa for local symbolic facts and lightweight inference.
- Letta for optional persistent stateful-agent memory.

Both integrations are deliberately optional at runtime: Bitey must remain
operational if either provider is unavailable. Supabase remains the business
source of truth and Groq remains the primary LLM provider.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


try:
    from hyperon import MeTTa, E, S
except Exception:  # pragma: no cover - optional native dependency
    MeTTa = None
    E = S = None

try:
    from letta_client import Letta
except Exception:  # pragma: no cover - optional network dependency
    Letta = None


class CognitiveEngine:
    def __init__(self) -> None:
        self.hyperon_enabled = str(os.getenv("BITEY_HYPERON_ENABLED", "true")).lower() in {"1", "true", "yes", "on"}
        self.letta_enabled = str(os.getenv("BITEY_LETTA_ENABLED", "true")).lower() in {"1", "true", "yes", "on"}
        self._metta = None
        self._letta = None
        self._letta_agent_id = os.getenv("LETTA_AGENT_ID", "").strip()
        self._initialize_hyperon()
        self._initialize_letta()

    def _initialize_hyperon(self) -> None:
        if not self.hyperon_enabled or MeTTa is None:
            return
        try:
            self._metta = MeTTa()
            self._metta.run("(= (bitey-fact $x $y) (fact $x $y))")
        except Exception as exc:
            print("[COGNITIVE][HYPERON] unavailable:", exc)
            self._metta = None

    def _initialize_letta(self) -> None:
        key = os.getenv("LETTA_API_KEY", "").strip()
        if not self.letta_enabled or not key or Letta is None:
            return
        try:
            self._letta = Letta(api_key=key)
        except Exception as exc:
            print("[COGNITIVE][LETTA] unavailable:", exc)
            self._letta = None

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "hyperon": bool(self._metta),
            "letta": bool(self._letta and self._letta_agent_id),
            "letta_configured": bool(self._letta),
        }

    def observe(self, *, customer_id: int, conversation_id: str, message: str,
                intent: Optional[str] = None, service_id: Optional[int] = None,
                confidence: float = 0.0) -> Dict[str, Any]:
        """Record a compact cognitive observation without changing business truth."""
        result: Dict[str, Any] = {"status": "observed", "components": self.status}

        if self._metta:
            try:
                # Facts are scoped by customer/conversation and are intentionally
                # descriptive; authoritative data remains in Supabase.
                self._metta.run(
                    f'(add-atom (BiteyObservation "{conversation_id}" "{intent or "unknown"}" {float(confidence):.4f}))'
                )
                result["hyperon_observed"] = True
            except Exception as exc:
                result["hyperon_error"] = str(exc)

        if self._letta and self._letta_agent_id:
            try:
                content = (
                    f"Bitey observation: customer={customer_id}; conversation={conversation_id}; "
                    f"intent={intent or 'unknown'}; service_id={service_id}; confidence={confidence:.4f}; "
                    f"message={message[:1200]}"
                )
                self._letta.agents.messages.create(
                    agent_id=self._letta_agent_id,
                    messages=[{"role": "user", "content": content}],
                )
                result["letta_observed"] = True
            except Exception as exc:
                result["letta_error"] = str(exc)

        return result


_engine: Optional[CognitiveEngine] = None


def get_cognitive_engine() -> CognitiveEngine:
    global _engine
    if _engine is None:
        _engine = CognitiveEngine()
    return _engine


def cognitive_observe(**kwargs: Any) -> Dict[str, Any]:
    return get_cognitive_engine().observe(**kwargs)


def cognitive_status() -> Dict[str, Any]:
    return get_cognitive_engine().status
