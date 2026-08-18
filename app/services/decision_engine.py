"""BiteFixes Decision Engine V18."""

from typing import Any, Dict, Optional

from app.services.company_service import get_company_context
from app.services.business_reasoning_service import resolve_business_reasoning
from app.services.service_resolver import resolve_service
from app.services.workflows.workflow_service import execute_workflow
from app.services.sales_engine import generate_sales_response

SALES_INTENTS = {"ai_assistant", "sales", "quote", "purchase"}
SUPPORT_INTENTS = {
    "computer_repair", "hardware_upgrade", "windows_installation",
    "mobile_repair", "cctv_installation", "camera_installation",
    "network_configuration", "software_problem", "remote_support",
    "cctv_repair", "cctv_configuration", "camera_replacement",
    "wifi_configuration", "router_configuration", "vpn_configuration",
    "network_diagnosis", "server_support", "microsoft365_support",
    "cloud_support", "data_recovery", "virus_malware", "performance_problem",
    "screen_repair", "battery_replacement", "charging_port", "camera_repair",
    "software_mobile", "data_transfer",
}
QUOTE_INTENTS = {
    "ai_assistant", "sales", "quote", "purchase", "cctv_installation",
    "camera_installation", "network_configuration", "hardware_upgrade",
}

GREETING_WORDS = {
    "hola", "hello", "hi", "hey", "oi", "ola", "buenas", "buenos dias",
    "buenas tardes", "buenas noches", "bom dia", "boa tarde", "boa noite",
}


def _reasoning_response(reasoning: Dict[str, Any], language: Optional[str]) -> Optional[str]:
    step = reasoning.get("next_step")
    if not step:
        return None
    if step.get("type") == "collect_requirements":
        requirements = step.get("requirements", [])
        names = [r.get("name") for r in requirements if r.get("name")]
        if not names:
            return None
        if language == "pt-BR":
            return "Para orientá-lo melhor, preciso de: " + ", ".join(names) + "."
        if language == "en":
            return "To guide you better, I need: " + ", ".join(names) + "."
        return "Para orientarte mejor, necesito: " + ", ".join(names) + "."
    if step.get("type") == "clarify_need":
        need = (step.get("needs") or [{}])[0]
        return need.get("description") or need.get("name")
    if step.get("type") == "present_solution":
        solution = (step.get("solutions") or [{}])[0]
        return solution.get("description") or solution.get("name")
    return None


def _is_greeting(message: str) -> bool:
    normalized = " ".join(str(message or "").lower().strip().split())
    return normalized in GREETING_WORDS


def make_decision(company_id: int, customer: Dict, message: str, intent: Dict, knowledge=None, memory=None, language=None, channel="unknown", business_context: Optional[Dict[str, Any]] = None):
    intent_name = intent.get("intent") if intent else None
    confidence = intent.get("confidence", 0) if intent else 0

    if business_context is None:
        try:
            business_context = get_company_context(company_id)
        except Exception as error:
            print("[BUSINESS CONTEXT WARNING]", error)
            business_context = None

    if not intent_name:
        if _is_greeting(message):
            greeting = {
                "pt-BR": "Olá! Sou Bitey. Como posso ajudá-lo?",
                "en": "Hello! I'm Bitey. How can I help you?",
            }.get(language, "Hola, soy Bitey. ¿Cómo puedo ayudarte?")
            return {"action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None, "response": greeting, "workflow": None, "service": None, "service_id": None, "reasoning": {}, "metadata": {"reason": "greeting"}}

        clarification = {
            "pt-BR": "Claro. Posso ajudá-lo com suporte técnico, celulares, computadores, redes, câmeras ou IA para empresas. O que você precisa?",
            "en": "Sure. I can help with technical support, phones, computers, networks, cameras, or business AI. What do you need?",
        }.get(language, "Claro. Puedo ayudarte con soporte técnico, celulares, computadoras, redes, cámaras o IA para empresas. ¿Qué necesitas?")
        return {"action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None, "response": clarification, "workflow": None, "service": None, "service_id": None, "reasoning": {}, "metadata": {"reason": "intent_not_detected"}}

    reasoning = resolve_business_reasoning(company_id, intent_name)
    service = resolve_service(company_id, intent_name, business_context=business_context)
    service_id = service.get("id") if service else None
    requires_quote = intent_name in QUOTE_INTENTS
    metadata = {
        "intent": intent_name,
        "confidence": confidence,
        "requires_quote": requires_quote,
        "business_context_loaded": bool(business_context),
        "ai_scope_loaded": bool(business_context and business_context.get("ai_scope")),
        "business_reasoning_found": reasoning.get("reasoning_found", False),
    }
    semantic_response = _reasoning_response(reasoning, language)

    if intent_name in SALES_INTENTS:
        response = semantic_response or generate_sales_response(intent_name, customer.get("full_name", "Cliente"), memory)
        return {"action": "sales", "create_ticket": True, "requires_quote": requires_quote, "ticket_type": "sales", "response": response, "service": service, "service_id": service_id, "workflow": None, "reasoning": reasoning, "metadata": metadata}

    if intent_name in SUPPORT_INTENTS:
        workflow_result = execute_workflow(
            intent=intent_name,
            company_id=company_id,
            customer_id=customer.get("id"),
            service_id=service_id,
            message=message,
            knowledge=knowledge,
            language=language,
            business_context=business_context,
            intent_data=intent,
        )
        workflow_ok = bool(workflow_result.get("success"))
        response = semantic_response or workflow_result.get("response") or "Voy a ayudarte con el diagnóstico."
        return {
            "action": "workflow",
            "create_ticket": workflow_ok,
            "requires_quote": requires_quote if workflow_ok else False,
            "ticket_type": "technical_support" if workflow_ok else None,
            "response": response,
            "workflow": intent_name,
            "workflow_result": workflow_result,
            "ticket": workflow_result.get("ticket"),
            "service": service,
            "service_id": service_id,
            "reasoning": reasoning,
            "metadata": metadata,
        }

    return {"action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None, "response": semantic_response or "Puedo ayudarte a identificar lo que necesitas. ¿Qué problema o servicio buscas?", "workflow": None, "service": service, "service_id": service_id, "reasoning": reasoning, "metadata": metadata}


def decision_engine(company_id, customer, message, intent, knowledge=None, memory=None, language=None, business_context=None):
    return make_decision(company_id, customer, message, intent, knowledge, memory, language, business_context=business_context)
