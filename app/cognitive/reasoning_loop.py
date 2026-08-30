"""Generic context-first reasoning coordinator.

This module deliberately contains no service-specific rules. It coordinates
existing identity, search, memory and decision components around one state.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .context_state import CognitiveState


class CognitiveReasoningLoop:
    """Build a stable cognitive packet before the LLM chooses a response."""

    def build_state(
        self,
        *,
        customer_id: Optional[int],
        company_id: Optional[int],
        conversation_id: Optional[str],
        language: str,
        message: str,
        memory: Optional[Dict[str, Any]] = None,
        intent: Optional[Dict[str, Any]] = None,
        problem: Optional[Dict[str, Any]] = None,
        business_context: Optional[Dict[str, Any]] = None,
    ) -> CognitiveState:
        state = CognitiveState(
            customer_id=customer_id,
            company_id=company_id,
            conversation_id=conversation_id,
            language=language or "pt-BR",
        )
        memory = memory or {}
        intent = intent or {}
        problem = problem or {}
        state.intent = intent.get("intent") or memory.get("last_intent")
        state.service_id = intent.get("service_id") or memory.get("last_service")
        state.active_problem = problem.get("problem") or memory.get("active_problem") or memory.get("last_problem")
        state.problem_state = str(problem.get("classification") or problem.get("state") or memory.get("problem_state") or "unknown")
        state.goal = memory.get("goal") or problem.get("goal") or state.intent
        state.known.update(memory.get("known") or {})
        state.known.update(problem.get("known") or {})
        state.entity.update(memory.get("entity") or {})
        state.entity.update(problem.get("entity") or {})
        state.missing = list(dict.fromkeys((memory.get("missing") or []) + (problem.get("missing") or [])))
        state.asked = list(dict.fromkeys(memory.get("asked") or []))
        state.confidence = float(intent.get("confidence") or problem.get("confidence") or 0.0)
        state.record_action("message_received", message=message[:500])
        return state

    def decide_next_action(self, state: CognitiveState, *, sufficient: Optional[bool] = None) -> str:
        """Choose an abstract action from state, without knowing any service domain."""
        if state.contradictions:
            return "resolve_contradiction"
        if sufficient is False or state.missing:
            return "ask_clarification"
        if not state.active_problem and not state.intent:
            return "understand"
        if state.next_action and state.next_action != "understand":
            return state.next_action
        if state.service_id or state.intent:
            return "advance_service"
        return "understand"

    def packet(self, state: CognitiveState, *, knowledge: Any = None, search: Any = None) -> Dict[str, Any]:
        state.next_action = self.decide_next_action(state)
        return {
            "state": state.to_dict(),
            "knowledge": knowledge or [],
            "search_evidence": search or [],
            "instruction": (
                "Interpret the current message inside this state. Preserve established facts. "
                "Do not restart service selection when the message answers pending questions. "
                "Choose the smallest next action that advances the active goal."
            ),
        }
