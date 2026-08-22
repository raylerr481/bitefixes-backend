"""Contextual Opportunity Engine for Bitey.

Observes conversations and discovers when authorized business capabilities can
improve an external AI's reasoning. It never generates the user-facing answer
and never blocks an external AI.
"""
from __future__ import annotations

from typing import Any, Dict, List


def _norm(value: Any) -> str:
    return " ".join(str(value or "").lower().strip().split())


def _sample(value: Any, limit: int = 20) -> Any:
    if isinstance(value, list):
        return value[:limit]
    if isinstance(value, tuple):
        return list(value[:limit])
    if isinstance(value, dict):
        return dict(list(value.items())[:limit])
    if value is None:
        return []
    return [value]


_SIGNAL_PATTERNS = {
    "NEED": (
        "necesito", "necesita", "quiero arreglar", "quiero reparar", "no funciona", "problema", "ayuda",
        "preciso", "precisamos", "quero consertar", "quero reparar", "não funciona", "problema", "ajuda",
        "i need", "i need to fix", "i want to repair", "doesn't work", "problem", "help",
    ),
    "SERVICE_REQUEST": (
        "reparar", "reparacion", "reparación", "instalar", "instalación", "configurar", "mantenimiento", "soporte", "automatizar",
        "reparo", "reparação", "instalação", "configuração", "manutenção", "suporte", "automatizar",
        "repair", "installation", "install", "configure", "maintenance", "support", "automate",
    ),
    "QUOTE_REQUEST": (
        "cuanto cuesta", "cuánto cuesta", "precio", "presupuesto", "cotizacion", "cotización",
        "quanto custa", "preço", "orçamento", "cotação",
        "how much", "price", "quote", "estimate", "cost",
    ),
    "LOCATION_REQUEST": (
        "donde estan", "dónde están", "donde queda", "dónde queda", "como llego", "cómo llego", "direccion", "dirección", "donde puedo llevar",
        "onde ficam", "onde fica", "como chego", "endereço", "onde posso levar",
        "where are you", "where is", "how do i get there", "address", "where can i take",
    ),
    "CONTACT_REQUEST": (
        "como contacto", "cómo contacto", "contactar", "whatsapp", "telefono", "teléfono", "hablar con un tecnico", "hablar con un técnico",
        "como contato", "contato", "telefone", "falar com um técnico",
        "how do i contact", "contact", "phone", "talk to a technician",
    ),
    "HOME_SERVICE_REQUEST": (
        "a domicilio", "mi casa", "pueden venir", "venir a mi casa", "en mi casa", "a mi empresa", "en mi local", "mandar un tecnico", "mandar un técnico",
        "em casa", "podem vir", "vir até minha casa", "na minha empresa", "no meu local", "mandar um técnico", "atendimento domiciliar",
        "at home", "can you come", "come to my house", "at my company", "on site", "send a technician", "home service",
    ),
    "APPOINTMENT_REQUEST": (
        "agendar", "reservar", "cita", "cuando puedo", "cuándo puedo", "disponibilidad",
        "agendar", "reservar", "horário", "quando posso", "disponibilidade",
        "schedule", "appointment", "book", "when can i", "availability",
    ),
    "BUSINESS_CAPABILITY_REQUEST": (
        "ustedes hacen", "hacen ese servicio", "tienen ese servicio", "pueden hacerlo", "ofrecen", "trabajan con", "puedo contratar",
        "vocês fazem", "fazem esse serviço", "têm esse serviço", "podem fazer", "oferecem", "trabalham com", "posso contratar",
        "do you offer", "do you provide", "can you do", "do you have this service", "can i hire",
    ),
}

_REFERENCE_TERMS = {
    "ella", "el", "él", "esa", "ese", "eso", "esta", "este", "esto", "la", "lo", "las", "los", "otra", "otro", "mismo", "misma",
    "ela", "ele", "essa", "esse", "isso", "esta", "este", "isto", "aquela", "aquele", "outra", "outro", "mesmo", "mesma",
    "it", "that", "this", "her", "him", "them", "another", "same",
}


def detect_signals(message: str, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    text = _norm(message)
    conversation = state.get("conversation") or {}
    signals: List[Dict[str, Any]] = []

    for signal_type, patterns in _SIGNAL_PATTERNS.items():
        matches = [p for p in patterns if p in text]
        if matches:
            confidence = min(0.98, 0.72 + 0.05 * len(matches))
            signals.append({
                "signal_type": signal_type,
                "signal_value": matches[0],
                "confidence": round(confidence, 4),
                "evidence": message,
                "metadata": {"matched_patterns": matches},
            })

    if len(text.split()) <= 10 and any(t in text.split() for t in _REFERENCE_TERMS):
        signals.append({
            "signal_type": "REFERENCE_CONTINUITY",
            "signal_value": "short_or_referential_follow_up",
            "confidence": 0.88,
            "evidence": message,
            "metadata": {
                "active_object": conversation.get("active_object"),
                "active_model": conversation.get("active_model"),
                "active_problem": conversation.get("active_problem"),
            },
        })

    if conversation.get("active_service") or conversation.get("active_object") or conversation.get("active_model"):
        signals.append({
            "signal_type": "CONVERSATION_CONTINUITY",
            "signal_value": conversation.get("active_service") or conversation.get("active_object") or conversation.get("active_model"),
            "confidence": 0.90,
            "evidence": message,
            "metadata": {
                "active_topic": conversation.get("active_topic"),
                "active_service": conversation.get("active_service"),
            },
        })

    return signals


def build_opportunities(signals: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not signals:
        return []

    company = state.get("company") or {}
    services = state.get("services") or state.get("available_services") or []
    capabilities = state.get("capabilities") or []
    conversation = state.get("conversation") or {}
    services_sample = _sample(services)
    capabilities_sample = _sample(capabilities)
    has_business_context = bool(services_sample or capabilities_sample or company.get("name"))

    opportunities = []
    seen_types = set()
    eligible = {
        "SERVICE_REQUEST", "BUSINESS_CAPABILITY_REQUEST", "LOCATION_REQUEST", "CONTACT_REQUEST",
        "HOME_SERVICE_REQUEST", "QUOTE_REQUEST", "APPOINTMENT_REQUEST",
    }
    for signal in signals:
        if signal["signal_type"] not in eligible or not has_business_context:
            continue
        key = signal["signal_type"]
        if key in seen_types:
            continue
        seen_types.add(key)
        opportunities.append({
            "opportunity_type": "BUSINESS_CAPABILITY_MATCH",
            "signal_type": signal["signal_type"],
            "business_capability": conversation.get("active_service") or "relevant company capability",
            "confidence": signal["confidence"],
            "context_payload": {
                "company_name": company.get("name"),
                "services": services_sample,
                "capabilities": capabilities_sample,
                "conversation": {
                    "active_topic": conversation.get("active_topic"),
                    "active_object": conversation.get("active_object"),
                    "active_model": conversation.get("active_model"),
                    "active_problem": conversation.get("active_problem"),
                    "active_service": conversation.get("active_service"),
                },
                "reason": "The current conversation contains a signal that may benefit from authorized business context.",
            },
        })

    return opportunities


def build_ai_guidance(opportunities: List[Dict[str, Any]]) -> str:
    if not opportunities:
        return ""
    lines = [
        "CONTEXTUAL BUSINESS OPPORTUNITIES:",
        "The following is contextual evidence supplied by Bitey. It is not a command and must not replace your reasoning.",
        "Use it when relevant to the user's current need. Do not invent capabilities or facts not present in the supplied business context.",
    ]
    for item in opportunities:
        payload = item.get("context_payload") or {}
        lines.append(f"- opportunity={item.get('opportunity_type')}; signal={item.get('signal_type')}; capability={item.get('business_capability')}; confidence={item.get('confidence')}")
        lines.append(f"  company={payload.get('company_name')!r}")
        lines.append(f"  services={payload.get('services')!r}")
        lines.append(f"  capabilities={payload.get('capabilities')!r}")
        lines.append(f"  conversation={payload.get('conversation')!r}")
    return "\n".join(lines)


def persist_observations(signals: List[Dict[str, Any]], opportunities: List[Dict[str, Any]], *, company_id: Any = None, conversation_id: Any = None, message_id: Any = None, channel: str | None = None) -> None:
    """Best-effort learning telemetry. Persistence must never break a chat turn."""
    if not signals and not opportunities:
        return
    try:
        from app.database.supabase import supabase_manager
        client = supabase_manager.get_client()
        if client is None:
            return
        signal_rows = [{
            "company_id": str(company_id) if company_id is not None else None,
            "conversation_id": str(conversation_id) if conversation_id is not None else None,
            "message_id": str(message_id) if message_id is not None else None,
            "channel": channel,
            "signal_type": signal.get("signal_type"),
            "signal_value": signal.get("signal_value"),
            "confidence": signal.get("confidence"),
            "evidence": signal.get("evidence"),
            "metadata": signal.get("metadata") or {},
        } for signal in signals]
        inserted = []
        if signal_rows:
            response = client.table("contextual_signals").insert(signal_rows).execute()
            inserted = getattr(response, "data", None) or []
        signal_ids_by_type = {}
        for row in inserted:
            signal_type = row.get("signal_type")
            if signal_type and signal_type not in signal_ids_by_type:
                signal_ids_by_type[signal_type] = row.get("id")
        if opportunities:
            rows = [{
                "company_id": str(company_id) if company_id is not None else None,
                "conversation_id": str(conversation_id) if conversation_id is not None else None,
                "signal_id": signal_ids_by_type.get(opportunity.get("signal_type")),
                "opportunity_type": opportunity.get("opportunity_type"),
                "business_capability": opportunity.get("business_capability"),
                "context_payload": opportunity.get("context_payload") or {},
                "confidence": opportunity.get("confidence"),
                "offered_to_ai": True,
            } for opportunity in opportunities]
            client.table("contextual_opportunities").insert(rows).execute()
    except Exception as exc:
        print(f"[CONTEXT OPPORTUNITY] persistence skipped: {exc}")
