"""Contextual Need Resolution (CNRA) for Bitey."""
from __future__ import annotations
from typing import Any, Dict


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def resolve_context(*, message: str, business_context: Dict[str, Any] | None,
                    memory: Dict[str, Any] | None, intent: Dict[str, Any] | None) -> Dict[str, Any]:
    ctx, mem, it = business_context or {}, memory or {}, intent or {}
    text = _text(message)
    active_service = mem.get("last_service") or it.get("service_id")
    active_topic = mem.get("active_topic") or mem.get("topic")
    active_object = mem.get("active_object")
    short_followup = len(text.split()) <= 6 and bool(active_object or active_topic or active_service)
    reference_terms = {"ella", "él", "el", "esa", "ese", "eso", "quebrada", "roto", "rota", "sí", "si", "esa misma"}
    contextual_reference = short_followup or bool(set(text.split()) & reference_terms)
    return {
        "company": {
            "id": ctx.get("company_id"), "name": ctx.get("company_name") or ctx.get("name") or "",
            "domain": ctx.get("domain") or ctx.get("business_type") or "",
            "objectives": ctx.get("objectives") or [], "directives": ctx.get("directives") or ctx.get("policies") or [],
            "vocabulary": ctx.get("vocabulary") or {},
        },
        "available_services": ctx.get("services") or ctx.get("service_catalog") or [],
        "capabilities": ctx.get("capabilities") or [],
        "conversation": {
            "active_topic": active_topic, "active_object": active_object, "active_service": active_service,
            "history": mem.get("history") or [], "stage": mem.get("stage") or "exploration",
            "contextual_reference": contextual_reference,
        },
        "need": {"raw": message, "intent": it.get("intent"), "confidence": it.get("confidence"), "missing": []},
        "governance": {
            "ticket_allowed": False, "catalog_only_if_requested": True,
            "invented_business_facts_forbidden": True, "external_ai_is_reasoning_authority": True,
        },
    }


def contextual_directive(state: Dict[str, Any]) -> str:
    company, conversation, need = state.get("company", {}), state.get("conversation", {}), state.get("need", {})
    return f"""CONTEXTUAL RESOLUTION RULES:
1. Work only inside the active company's context: {company.get('name') or 'the current company'}.
2. The external AI is the reasoning authority. Bitey supplies context, memory, tools and evaluation; do not invent business facts.
3. Answer the user's detected need, not the whole service catalog. Show the catalog only if the user asks what services are available.
4. Preserve continuity: topic={conversation.get('active_topic')!r}; object={conversation.get('active_object')!r}; service={conversation.get('active_service')!r}; stage={conversation.get('stage')!r}.
5. If this is a short contextual follow-up, inherit the active object before asking what the user means.
6. Ask the smallest question needed to advance the current need. Do not restart the conversation.
7. A detected service is not a ticket. Ticket_allowed={state.get('governance', {}).get('ticket_allowed')}; require mature explicit commitment before action.
8. If an external fact is needed, use the governed web-search capability and incorporate its evidence.
9. Current need: {need.get('raw')!r}; detected intent={need.get('intent')!r}.
""".strip()
