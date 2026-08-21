"""BiteFixes Decision Engine V23 — governed reasoning and AI consultation."""
from typing import Any, Dict, Optional
from app.services.company_service import get_company_context
from app.services.business_reasoning_service import resolve_business_reasoning
from app.services.service_resolver import resolve_service
from app.services.workflows.workflow_service import execute_workflow
from app.services.sales_engine import generate_sales_response

try:
    from app.services.ai_provider import ai_provider
    from app.ai.consultation_gate import evaluate as evaluate_ai_consultation
    from app.ai.ai_council import consult as consult_ai
    from app.ai.evaluator import evaluate_candidates
except Exception:
    ai_provider = evaluate_ai_consultation = consult_ai = evaluate_candidates = None

SALES_INTENTS = {"ai_assistant", "sales", "quote", "purchase"}
SUPPORT_INTENTS = {"computer_repair", "hardware_upgrade", "windows_installation", "mobile_repair", "cctv_installation", "camera_installation", "network_configuration", "software_problem", "remote_support", "cctv_repair", "cctv_configuration", "camera_replacement", "wifi_configuration", "router_configuration", "vpn_configuration", "network_diagnosis", "server_support", "microsoft365_support", "cloud_support", "data_recovery", "virus_malware", "performance_problem", "screen_repair", "battery_replacement", "charging_port", "camera_repair", "software_mobile", "data_transfer"}
QUOTE_INTENTS = {"ai_assistant", "sales", "quote", "purchase", "cctv_installation", "camera_installation", "network_configuration", "hardware_upgrade"}
GREETING_WORDS = {"hola", "hello", "hi", "hey", "oi", "ola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "bom dia", "boa tarde", "boa noite"}


def _reasoning_response(reasoning: Dict[str, Any], language: Optional[str]) -> Optional[str]:
    step = reasoning.get("next_step")
    if not step:
        return None
    if step.get("type") == "collect_requirements":
        names = [r.get("name") for r in step.get("requirements", []) if r.get("name")]
        if not names:
            return None
        return {"pt-BR": "Para orientá-lo melhor, preciso de: ", "en": "To guide you better, I need: "}.get(language, "Para orientarte mejor, necesito: ") + ", ".join(names) + "."
    if step.get("type") == "clarify_need":
        need = (step.get("needs") or [{}])[0]
        return need.get("description") or need.get("name")
    if step.get("type") == "present_solution":
        solution = (step.get("solutions") or [{}])[0]
        return solution.get("description") or solution.get("name")
    return None


def _is_greeting(message: str) -> bool:
    return " ".join(str(message or "").lower().strip().split()) in GREETING_WORDS


def _external_consultation(message: str, language: Optional[str], intent: Dict[str, Any], business_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not all((evaluate_ai_consultation, consult_ai, ai_provider)) or not ai_provider.available():
        return {"ai_used": False, "reason": "provider_unavailable"}
    confidence = float(intent.get("confidence", 0) or 0)
    complexity = 0.8 if len(message) > 240 else 0.3
    novelty = 0.8 if not intent.get("intent") else 0.3
    gap = 0.8 if not intent.get("intent") else 0.2
    impact = 0.7 if intent.get("intent") in {"ai_assistant", "sales", "quote"} else 0.2
    gate = evaluate_ai_consultation(confidence=confidence, complexity=complexity, novelty=novelty, knowledge_gap=gap, business_impact=impact, estimated_cost=0.0)
    if not gate.consult:
        return {"ai_used": False, "reason": gate.reason, "gate_value": gate.estimated_value}
    candidates = consult_ai(message, language=language or "es", context={"intent": intent, "business_context": business_context or {}}, max_providers=gate.max_providers)
    evaluation = evaluate_candidates(candidates, core_confidence=confidence) if evaluate_candidates else {"status": "not_evaluated"}
    return {"ai_used": bool(candidates), "gate_reason": gate.reason, "gate_value": gate.estimated_value, "candidates": candidates, "evaluation": evaluation, "learning_candidate": bool(evaluation.get("learning_candidate"))}


def make_decision(company_id: int, customer: Dict, message: str, intent: Dict, knowledge=None, memory=None, language=None, channel="unknown", business_context: Optional[Dict[str, Any]] = None):
    intent = intent or {}
    if business_context is None:
        try:
            business_context = get_company_context(company_id)
        except Exception as error:
            print("[BUSINESS CONTEXT WARNING]", error)
            business_context = None

    ai_metadata = _external_consultation(message, language, intent, business_context)
    intent_name = intent.get("intent")
    confidence = float(intent.get("confidence", 0) or 0)

    if not intent_name:
        if _is_greeting(message):
            greeting = {"pt-BR": "Olá! Sou Bitey. Como posso ajudá-lo?", "en": "Hello! I'm Bitey. How can I help?"}.get(language, "Hola, soy Bitey. ¿Cómo puedo ayudarte?")
            return {"action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None, "response": greeting, "workflow": None, "service": None, "service_id": None, "reasoning": {}, "metadata": {"reason": "greeting", **ai_metadata}}
        clarification = {"pt-BR": "Claro. Posso ajudá-lo com suporte técnico, celulares, computadores, redes, câmeras ou IA para empresas. O que você precisa?", "en": "Sure. I can help with technical support, phones, computers, networks, cameras, or business AI. What do you need?"}.get(language, "Claro. Puedo ayudarte con soporte técnico, celulares, computadoras, redes, cámaras o IA para empresas. ¿Qué necesitas?")
        return {"action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None, "response": clarification, "workflow": None, "service": None, "service_id": None, "reasoning": {}, "metadata": {"reason": "intent_not_detected", **ai_metadata}}

    reasoning = resolve_business_reasoning(company_id, intent_name)
    service = resolve_service(company_id, intent_name, business_context=business_context)
    service_id = service.get("id") if service else None
    requires_quote = intent_name in QUOTE_INTENTS
    metadata = {"intent": intent_name, "confidence": confidence, "requires_quote": requires_quote, "business_context_loaded": bool(business_context), "ai_scope_loaded": bool(business_context and business_context.get("ai_scope")), "business_reasoning_found": reasoning.get("reasoning_found", False), **ai_metadata}
    semantic_response = _reasoning_response(reasoning, language)

    if intent_name in SALES_INTENTS:
        return {"action": "sales", "create_ticket": True, "requires_quote": requires_quote, "ticket_type": "sales", "response": semantic_response or generate_sales_response(intent_name, customer.get("full_name", "Cliente"), memory), "service": service, "service_id": service_id, "workflow": None, "reasoning": reasoning, "metadata": metadata}

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
            memory=memory,
        )
        ok = bool(workflow_result.get("success"))
        response = semantic_response or workflow_result.get("response") or "Voy a ayudarte con el diagnóstico."
        return {"action": "workflow", "create_ticket": ok, "requires_quote": requires_quote if ok else False, "ticket_type": "technical_support" if ok else None, "response": response, "workflow": intent_name, "workflow_result": workflow_result, "ticket": workflow_result.get("ticket"), "service": service, "service_id": service_id, "reasoning": reasoning, "metadata": metadata}

    return {"action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None, "response": semantic_response or "Puedo ayudarte a identificar lo que necesitas. ¿Qué problema o servicio buscas?", "workflow": None, "service": service, "service_id": service_id, "reasoning": reasoning, "metadata": metadata}


def decision_engine(company_id, customer, message, intent, knowledge=None, memory=None, language=None, business_context=None):
    return make_decision(company_id, customer, message, intent, knowledge, memory, language, business_context=business_context)
