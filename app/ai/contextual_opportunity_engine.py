"""Contextual Opportunity Engine for Bitey.

This layer observes conversations and discovers when authorized business
capabilities can improve an external AI's reasoning. It never generates the
user-facing answer and never blocks an external AI.
"""
from __future__ import annotations

from typing import Any, Dict, List


def _norm(value: Any) -> str:
    return " ".join(str(value or "").lower().strip().split())


_SIGNAL_PATTERNS = {
    "NEED": ("necesito", "necesita", "quiero arreglar", "quiero reparar", "no funciona", "problema", "ayuda"),
    "SERVICE_REQUEST": ("reparar", "reparacion", "reparación", "instalar", "instalación", "configurar", "mantenimiento", "soporte", "automatizar"),
    "QUOTE_REQUEST": ("cuanto cuesta", "cuánto cuesta", "precio", "presupuesto", "cotizacion", "cotización"),
    "LOCATION_REQUEST": ("donde estan", "dónde están", "donde queda", "dónde queda", "como llego", "cómo llego", "direccion", "dirección", "donde puedo llevar"),
    "CONTACT_REQUEST": ("como contacto", "cómo contacto", "contactar", "whatsapp", "telefono", "teléfono", "hablar con un tecnico", "hablar con un técnico"),
    "HOME_SERVICE_REQUEST": ("a domicilio", "mi casa", "pueden venir", "venir a mi casa", "en mi casa", "a mi empresa", "en mi local", "mandar un tecnico", "mandar un técnico"),
    "APPOINTMENT_REQUEST": ("agendar", "reservar", "cita", "cuando puedo", "cuándo puedo", "disponibilidad", "mañana", "hoy"),
    "BUSINESS_CAPABILITY_REQUEST": ("ustedes hacen", "hacen ese servicio", "tienen ese servicio", "pueden hacerlo", "ofrecen", "trabajan con", "puedo contratar"),
}

_REFERENCE_TERMS = {"ella", "el", "él", "esa", "ese", "eso", "esta", "este", "esto", "la", "lo", "las", "los", "otra", "otro", "mismo", "misma"}


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
            "metadata": {"active_object": conversation.get("active_object"), "active_model": conversation.get("active_model"), "active_problem": conversation.get("active_problem")},
        })

    if conversation.get("active_service") or conversation.get("active_object") or conversation.get("active_model"):
        signals.append({
            "signal_type": "CONVERSATION_CONTINUITY",
            "signal_value": conversation.get("active_service") or conversation.get("active_object") or conversation.get("active_model"),
            "confidence": 0.90,
            "evidence": message,
            "metadata": {"active_topic": conversation.get("active_topic"), "active_service": conversation.get("active_service")},
        })

    return signals


def build_opportunities(signals: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not signals:
        return []

    company = state.get("company") or {}
    services = state.get("available_services") or []
    capabilities = state.get("capabilities") or []
    conversation = state.get("conversation") or {}

    # Do not force a service mapping here. The external AI remains the reasoning authority.
    service_text = " ".join(str(s) for s in services[:50])
    capability_text = " ".join(str(c) for c in capabilities[:50])
    has_business_context = bool(service_text or capability_text or company.get("name"))

    opportunities = []
    for signal in signals:
        if signal["signal_type"] in {"SERVICE_REQUEST", "BUSINESS_CAPABILITY_REQUEST", "LOCATION_REQUEST", "CONTACT_REQUEST", "HOME_SERVICE_REQUEST", "QUOTE_REQUEST", "APPOINTMENT_REQUEST"} and has_business_context:
            opportunities.append({
                "opportunity_type": "BUSINESS_CAPABILITY_MATCH",
                "business_capability": conversation.get("active_service") or "relevant company capability",
                "confidence": signal["confidence"],
                "context_payload": {
                    "company_name": company.get("name"),
                    "services": services[:20],
                    "capabilities": capabilities[:20],
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
        lines.append(f"- opportunity={item.get('opportunity_type')}; capability={item.get('business_capability')}; confidence={item.get('confidence')}")
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
        signal_rows = []
        for signal in signals:
            signal_rows.append({
                "company_id": str(company_id) if company_id is not None else None,
                "conversation_id": str(conversation_id) if conversation_id is not None else None,
                "message_id": str(message_id) if message_id is not None else None,
                "channel": channel,
                "signal_type": signal.get("signal_type"),
                "signal_value": signal.get("signal_value"),
                "confidence": signal.get("confidence"),
                "evidence": signal.get("evidence"),
                "metadata": signal.get("metadata") or {},
            })
        inserted = []
        if signal_rows:
            response = client.table("contextual_signals").insert(signal_rows).execute()
            inserted = getattr(response, "data", None) or []
        if opportunities:
            rows = []
            for index, opportunity in enumerate(opportunities):
                rows.append({
                    "company_id": str(company_id) if company_id is not None else None,
                    "conversation_id": str(conversation_id) if conversation_id is not None else None,
                    "signal_id": inserted[index].get("id") if index < len(inserted) else None,
                    "opportunity_type": opportunity.get("opportunity_type"),
                    "business_capability": opportunity.get("business_capability"),
                    "context_payload": opportunity.get("context_payload") or {},
                    "confidence": opportunity.get("confidence"),
                    "offered_to_ai": True,
                })
            client.table("contextual_opportunities").insert(rows).execute()
    except Exception as exc:
        # Observability only: never turn a learning-table failure into an AI failure.
        print(f"[CONTEXT OPPORTUNITY] persistence skipped: {exc}")
