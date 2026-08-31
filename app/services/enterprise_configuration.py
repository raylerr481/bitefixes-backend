"""Bitey Enterprise configuration assessment helpers.

This module does not replace BiteFixes CRM behavior. It defines the minimum
business configuration Bitey needs before adapting the same core to another
tenant. The result is deterministic and can be used by the conversational
assessment flow before producing an installable tenant configuration.
"""
from __future__ import annotations

from typing import Any

REQUIRED_SECTIONS = (
    "identity",
    "business",
    "services",
    "customers",
    "employees",
    "crm",
    "channels",
    "knowledge",
    "ai",
    "permissions",
)

OPTIONAL_SECTIONS = (
    "sales",
    "finance",
    "analytics",
    "automation",
    "integrations",
)

CHANNELS = ("whatsapp", "telegram", "website")


def assess_enterprise_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Return missing information and safe next questions for a tenant.

    This function only evaluates the supplied profile. It never invents
    business facts and never grants permissions.
    """
    profile = profile or {}
    missing = [section for section in REQUIRED_SECTIONS if not profile.get(section)]

    identity = profile.get("identity") or {}
    business = profile.get("business") or {}
    channels = profile.get("channels") or {}
    enabled_channels = channels.get("enabled") if isinstance(channels, dict) else None
    if not enabled_channels:
        missing.append("channels.enabled")

    questions: list[str] = []
    if not identity.get("company_name"):
        questions.append("Qual é o nome comercial da empresa?")
    if not business.get("industry"):
        questions.append("Qual é a atividade ou setor principal da empresa?")
    if not profile.get("services"):
        questions.append("Quais produtos ou serviços devem estar disponíveis para Bitey?")
    if not profile.get("employees"):
        questions.append("Quais funções ou equipes utilizarão o Portal?")
    if not enabled_channels:
        questions.append("Quais canais devem ficar ativos: WhatsApp, Telegram e/ou Web?")
    if not profile.get("knowledge"):
        questions.append("Qué documentos, políticas, catálogos o procedimientos puede utilizar Bitey como conocimiento empresarial?")
    if not profile.get("ai"):
        questions.append("Qué funciones de IA desea activar inicialmente?")
    if not profile.get("permissions"):
        questions.append("Qué roles pueden consultar clientes, ventas, servicios y tickets?")

    recommendations: list[str] = []
    if "crm" in profile and profile.get("crm"):
        recommendations.append("Conservar el ciclo Customer → Conversation → Lead → Opportunity → Sale → Service → Ticket.")
    if enabled_channels:
        recommendations.append("Usar un único Conversation Engine y mantener el tenant como contexto autoritativo.")
    recommendations.append("Generar una versión de configuración antes de instalar y permitir rollback a la versión anterior.")
    recommendations.append("Mantener secretos, permisos y decisiones críticas en el backend; el documento empresarial aporta contexto, no autoridad.")

    return {
        "status": "assessment_ready",
        "complete": not missing,
        "required_sections": list(REQUIRED_SECTIONS),
        "optional_sections": list(OPTIONAL_SECTIONS),
        "missing": missing,
        "next_questions": questions,
        "recommendations": recommendations,
        "supported_customer_channels": list(CHANNELS),
        "configuration_ready": not missing,
    }


def build_configuration_manifest(profile: dict[str, Any], *, version: str = "1.0") -> dict[str, Any]:
    """Build a non-secret tenant manifest after assessment is complete."""
    assessment = assess_enterprise_profile(profile)
    if not assessment["complete"]:
        raise ValueError("Enterprise profile is incomplete: " + ", ".join(assessment["missing"]))

    identity = profile["identity"]
    channels = profile["channels"]
    return {
        "manifest": "bitey-enterprise",
        "version": version,
        "tenant": {
            "key": profile.get("tenant_key"),
            "company_name": identity.get("company_name"),
            "assistant_name": identity.get("assistant_name") or "Bitey",
            "white_label": bool(identity.get("white_label", True)),
        },
        "channels": channels,
        "modules": profile.get("ai", {}),
        "crm": profile.get("crm", {}),
        "permissions": profile.get("permissions", {}),
        "knowledge": profile.get("knowledge", {}),
        "status": "ready_for_review",
        "secrets": "server_side_only",
    }
