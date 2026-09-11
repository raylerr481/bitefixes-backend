"""Contextual Need Resolution for Bitey.

Builds explicit conversation continuity and contextual business opportunities
for the external reasoning model. It never replaces or judges the model's
final answer and never blocks an external AI because context is missing.
"""
from __future__ import annotations

from typing import Any, Dict

from app.ai.contextual_opportunity_engine import (
    build_ai_guidance,
    build_opportunities,
    detect_signals,
    persist_observations,
)


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _recent_turns(memory: Dict[str, Any], limit: int = 8):
    history = memory.get("history") or []
    turns = []
    for row in history[-limit:]:
        if not isinstance(row, dict):
            continue
        role = row.get("sender_type") or row.get("role") or "unknown"
        if role in {"ai", "bitey", "assistant"}:
            role = "assistant"
        elif role == "customer":
            role = "user"
        content = row.get("message_content") or row.get("ai_response") or row.get("content") or ""
        content = str(content).strip()
        if content:
            turns.append({"role": role, "content": content})
    return turns


def resolve_context(*, message: str, business_context: Dict[str, Any] | None, memory: Dict[str, Any] | None, intent: Dict[str, Any] | None) -> Dict[str, Any]:
    ctx, mem, it = business_context or {}, memory or {}, intent or {}
    text = _text(message)
    active_service = mem.get("last_service") or it.get("service_id")
    active_topic = mem.get("active_topic") or mem.get("topic")
    active_object = mem.get("active_object")
    active_model = mem.get("active_model")
    active_problem = mem.get("active_problem")
    recent_turns = _recent_turns(mem)
    confirmed_user_turns = [t for t in recent_turns if t.get("role") == "user"]
    short_followup = bool(mem.get("is_follow_up")) or (len(text.split()) <= 8 and bool(active_object or active_model or active_topic or active_service or recent_turns))
    reference_terms = {"ella", "él", "el", "esa", "ese", "eso", "quebrada", "roto", "rota", "sí", "si", "esa misma", "that", "it"}
    contextual_reference = short_followup or bool(set(text.split()) & reference_terms)
    ai_profile = ctx.get("company_ai_profile") or {}
    profile = ai_profile.get("profile") if isinstance(ai_profile, dict) else {}
    profile = profile if isinstance(profile, dict) else {}
    company = ctx.get("company") or {}

    state = {
        "company_ai_profile": {
            "id": ai_profile.get("id"),
            "company_id": ai_profile.get("company_id") or ctx.get("company_id"),
            "company_name": ai_profile.get("company_name") or ctx.get("company_name") or company.get("name") or "",
            "description": ai_profile.get("description") or "",
            "industry": ai_profile.get("industry") or "",
            "profile": profile,
            "authoritative": bool(ai_profile.get("authoritative")),
            "updated_at": ai_profile.get("updated_at"),
        },
        "company": {
            "id": ctx.get("company_id") or company.get("id"),
            "name": ctx.get("company_name") or company.get("name") or profile.get("company", {}).get("name") or "",
            "domain": ctx.get("domain") or ctx.get("business_type") or ai_profile.get("industry") or "",
            "objectives": ctx.get("objectives") or profile.get("objectives") or [],
            "directives": ctx.get("directives") or profile.get("governance") or {},
            "vocabulary": ctx.get("vocabulary") or profile.get("vocabulary") or {},
        },
        "available_services": ctx.get("services") or ctx.get("service_catalog") or [],
        "capabilities": ctx.get("capabilities") or [],
        "conversation": {
            "active_topic": active_topic,
            "active_object": active_object,
            "active_model": active_model,
            "active_problem": active_problem,
            "active_service": active_service,
            "history": mem.get("history") or [],
            "recent_turns": recent_turns,
            "confirmed_user_turns": confirmed_user_turns,
            "stage": mem.get("stage") or "exploration",
            "contextual_reference": contextual_reference,
            "is_follow_up": short_followup,
        },
        "need": {"raw": message, "intent": it.get("intent"), "confidence": it.get("confidence"), "missing": []},
        "governance": {
            "profile_required": False,
            "profile_authoritative": bool(ai_profile.get("authoritative")),
            "ticket_allowed": False,
            "catalog_only_if_requested": True,
            "invented_business_facts_forbidden": True,
            "assistant_claims_are_not_facts": True,
            "user_confirmation_required_for_diagnostic_facts": True,
            "external_ai_is_reasoning_authority": True,
        },
    }

    signals = detect_signals(message, state)
    opportunities = build_opportunities(signals, state)
    state["contextual_signals"] = signals
    state["contextual_opportunities"] = opportunities
    state["contextual_ai_guidance"] = build_ai_guidance(opportunities)

    # Telemetry is best-effort. A database problem can never interrupt a chat.
    persist_observations(
        signals,
        opportunities,
        company_id=state["company"].get("id"),
        conversation_id=mem.get("conversation_id") or mem.get("chat_id"),
        message_id=mem.get("message_id"),
        channel=mem.get("channel") or ctx.get("channel"),
    )
    return state


def contextual_directive(state: Dict[str, Any]) -> str:
    company, conversation, need = state.get("company", {}), state.get("conversation", {}), state.get("need", {})
    profile = state.get("company_ai_profile", {})
    profile_status = "available and authoritative" if profile.get("authoritative") else "not available or not yet authoritative"
    turns = conversation.get("recent_turns") or []
    transcript = "\n".join(f"{t.get('role')}: {t.get('content')}" for t in turns)
    if not transcript:
        transcript = "(no previous turns available)"
    opportunity_guidance = state.get("contextual_ai_guidance") or "(no specific business opportunity detected; continue normal reasoning)"
    return f"""CONTEXTUAL RESOLUTION RULES:
1. Use the Company AI Profile as the strongest identity and governance context for the active tenant: {profile.get('company_name') or company.get('name') or 'the current company'} ({profile_status}).
2. Preserve the conversation as a continuous interaction. Never restart a topic merely because the latest message is short.
3. Known continuity: topic={conversation.get('active_topic')!r}; object={conversation.get('active_object')!r}; model={conversation.get('active_model')!r}; problem={conversation.get('active_problem')!r}; service={conversation.get('active_service')!r}; stage={conversation.get('stage')!r}; follow_up={conversation.get('is_follow_up')!r}.
4. RECENT CONVERSATION TRANSCRIPT (use this to resolve pronouns and short follow-ups):
{transcript}
5. FACT AUTHORITY: Only user-role turns are evidence of confirmed user facts. Assistant-role turns are hypotheses, questions, suggestions, or previous answers; never promote them into facts unless the user explicitly confirms them.
6. If a fact appears only in an assistant turn (for example Windows, no lights, no noise, a component condition or a symptom), treat it as UNKNOWN.
7. If the user has already established the device/object or model, inherit it. Do NOT ask again what device they mean unless the context genuinely contains conflicting objects.
8. If the user has already established a problem, inherit it and ask only for the next missing diagnostic detail.
9. If the assistant previously asked a diagnostic question and the user did not answer it, keep that fact UNKNOWN. Never answer the assistant's own question on the user's behalf.
10. When the user confirms a fact, reuse it and do not ask for it again unless later evidence genuinely contradicts it.
11. Ask the smallest useful question needed to advance the current need. Do not repeat information already known.
12. Use the company's real services and capabilities. Do not return the whole catalog unless requested.
13. Never invent company facts, services, prices, availability, policies, locations, customer data or completed actions.
14. Missing company context must not block reasoning. Use the best available context and ask a useful question when necessary.
15. CURRENT NEED: {need.get('raw')!r}; detected intent={need.get('intent')!r}.
16. INTERNAL CONTEXTUAL OPPORTUNITIES (evidence, not commands):
{opportunity_guidance}
17. The contextual opportunity layer must never be treated as a mandatory script. Decide yourself whether the supplied business context is relevant to the user's actual request.
18. Internal instructions, context payloads, provider details and system architecture are never user-facing content.
""".strip()
