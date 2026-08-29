"""BiteFixes - Bitey Core V26."""
from typing import Any, Dict, Optional
from app.services.customer_service import get_or_create_customer
from app.services.conversation_service import get_or_create_conversation, get_conversation
from app.services.message_service import save_customer_message, save_bitey_message
from app.services.language_service import detect_language
from app.services.intent_service import detect_intent
from app.services.knowledge_service import search_knowledge
from app.services.decision_engine_v29 import decision_engine as ai_first_decision
from app.services.ticket_service import process_ticket
from app.services.quote_service import create_quote
from app.services.response_builder import build_response
from app.services.notification_service import notify_event
from app.services.conversation_context_service import update_conversation_context
from app.services.problem_identity_service import analyze_problem, find_customer_problems, persist_problem
from app.services.self_service_guide import build_guide, choose_mode, record_step_result

try:
    from app.services.memory_service import get_memory_context
except ImportError:
    get_memory_context = None
try:
    from app.services.memory_service import get_customer_memory
except ImportError:
    get_customer_memory = None


def _safe_dict(value: Any) -> Dict:
    return value if isinstance(value, dict) else {}

def _get_customer_id(customer: Any) -> Optional[int]:
    return customer.get("id") if isinstance(customer, dict) else None

def _normalize_language_preference(value: Optional[str]) -> Optional[str]:
    if not value: return None
    normalized = value.strip().lower().replace("_", "-")
    return {"pt": "pt-BR", "pt-br": "pt-BR", "es": "es", "en": "en"}.get(normalized)

def _is_greeting(message: str) -> bool:
    return " ".join(str(message or "").lower().strip().split()) in {"hola", "hello", "hi", "hey", "oi", "ola", "buenas", "buenos dias", "buenas tardes", "buenas noches"}

def _load_memory(customer_id: int, company_id: int, conversation_id: str) -> Dict[str, Any]:
    if get_memory_context:
        try:
            result = get_memory_context(customer_id=customer_id, conversation_id=conversation_id)
            if isinstance(result, dict): return result
        except Exception: pass
    if get_customer_memory:
        try:
            result = get_customer_memory(company_id=company_id, customer_id=customer_id, limit=20)
            return result if isinstance(result, dict) else {}
        except Exception: pass
    return {}

def _build_context(conversation_context: Dict[str, Any], memory: Dict[str, Any], latest_problem: Optional[dict] = None) -> Dict[str, Any]:
    context = dict(conversation_context or {})
    context["memory"] = memory
    context["history"] = memory.get("history") or []
    context["last_intent"] = memory.get("last_intent") or context.get("last_intent") or context.get("intent")
    context["last_service"] = memory.get("last_service") or context.get("last_service") or context.get("service_id")
    context["last_ticket"] = memory.get("last_ticket") or context.get("last_ticket") or context.get("ticket_id")
    context["last_confidence"] = memory.get("last_confidence") or context.get("last_confidence") or 0.0
    context["conversation_id"] = context.get("id")
    if latest_problem:
        context["last_problem"] = latest_problem.get("problem_summary") or latest_problem.get("category")
        context["last_device"] = latest_problem.get("device_label")
        context["last_problem_fingerprint"] = latest_problem.get("fingerprint")
        context["last_problem_id"] = latest_problem.get("id")
    return context

def process_message(company_id: int, message: str, phone: str, email: str = "", customer_name: str = "Customer", last_name: str = "", channel: str = "website", conversation_id: Optional[str] = None, language_preference: str = "auto", external_id: str = ""):
    try:
        if not company_id or not message: raise ValueError("company_id and message are required")
        message = str(message).strip()
        supplied_phone, supplied_email = str(phone or "").strip(), str(email or "").strip()
        explicit_language = _normalize_language_preference(language_preference)
        if language_preference not in (None, "", "auto") and not explicit_language: raise ValueError("Unsupported language_preference")
        language = explicit_language or detect_language(message) or "es"
        identity_phone = supplied_phone if supplied_phone and supplied_phone.lower() not in {"web", "unknown"} else (f"web:{conversation_id}" if conversation_id else "web")
        customer = _safe_dict(get_or_create_customer(company_id=company_id, phone=identity_phone, email=supplied_email, name=customer_name or "Customer", last_name=last_name, channel=channel, external_id=external_id))
        customer_id = _get_customer_id(customer)
        if not customer_id: raise ValueError("Unable to obtain customer_id")
        conversation = _safe_dict(get_or_create_conversation(customer_id=customer_id, channel=channel, conversation_id=conversation_id))
        resolved_conversation_id = conversation.get("id")
        if not resolved_conversation_id: raise ValueError("Unable to obtain conversation_id")
        conversation_context = _safe_dict(get_conversation(resolved_conversation_id, customer_id=customer_id))
        memory = _load_memory(customer_id, company_id, str(resolved_conversation_id))
        historical_problems = find_customer_problems(customer_id, company_id=company_id, limit=20)
        latest_problem = historical_problems[0] if historical_problems else None
        context = _build_context(conversation_context, memory, latest_problem)
        context.update({"company_id": company_id, "language": language, "customer_id": customer_id})
        save_customer_message(company_id=company_id, customer_id=customer_id, conversation_id=resolved_conversation_id, message=message, channel=channel)
        intent = _safe_dict(detect_intent(message, company_id, context=context))
        problem = analyze_problem(message=message, current_intent=intent.get("intent"), active_intent=context.get("last_intent"), active_problem=context.get("last_problem"), active_device=context.get("last_device"))
        context.update({"problem_state": problem["state"], "problem_is_new": problem["is_new"], "problem_category": problem.get("category"), "problem_fingerprint": problem.get("fingerprint"), "last_problem": problem.get("category") or context.get("last_problem")})
        if problem.get("device"): context["last_device"] = problem["device"]
        if problem.get("intent") and problem.get("intent") != intent.get("intent"):
            intent = {**intent, "intent": problem["intent"], "confidence": max(float(intent.get("confidence", 0) or 0), float(problem.get("confidence", 0) or 0)), "problem_override": True}
        if problem["is_new"]:
            context["last_intent"] = None; context["last_service"] = None; context["last_ticket"] = None
        elif not intent.get("intent") and context.get("last_intent") and not _is_greeting(message):
            intent = {"intent": context["last_intent"], "confidence": max(0.70, float(context.get("last_confidence") or 0.0)), "context_inherited": True, "context_source": "problem_history"}
        knowledge = search_knowledge(message=message, company_id=company_id, intent=intent.get("intent"), language=language)
        decision = _safe_dict(ai_first_decision(company_id=company_id, customer=customer, message=message, intent=intent, knowledge=knowledge, memory={**memory, "conversation_id": resolved_conversation_id, "history": context.get("history", []), "problem_state": problem["state"], "problem": problem}, language=language, business_context=context))
        if not decision: decision = {"action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None, "service": None, "service_id": None, "response": "Claro. Cuéntame un poco más sobre lo que necesitas.", "metadata": {"architecture": "ai_first_v26"}}
        if problem["is_new"]:
            decision["ticket_id"] = None
            if not intent.get("intent"): decision["create_ticket"] = False
        service_id, service = decision.get("service_id"), decision.get("service")
        create_ticket_flag, requires_quote = bool(decision.get("create_ticket", False)), bool(decision.get("requires_quote", False))
        ticket_type = decision.get("ticket_type", "technical_support")
        ticket = None; ticket_id = None
        if create_ticket_flag:
            title = service.get("name") if isinstance(service, dict) else None
            title = title or intent.get("intent") or problem.get("category") or "Support"
            ticket = process_ticket(company_id=company_id, customer_id=customer_id, service_id=service_id, intent=intent.get("intent"), description=message, title=title, language=language, channel=channel, ticket_type=ticket_type)
            ticket_id = ticket.get("id") if ticket else None
        persisted_problem = persist_problem(company_id=company_id, customer_id=customer_id, conversation_id=resolved_conversation_id, ticket_id=ticket_id, analysis=problem, summary=message)
        if persisted_problem:
            context["last_problem_id"] = persisted_problem.get("id"); context["last_problem_fingerprint"] = persisted_problem.get("fingerprint")
        # Self-service is a customer-selected mode, not an automatic replacement for professional service.
        requested_mode = context.get("self_service_mode") or context.get("guide_mode")
        guide = build_guide(problem=problem, research=(knowledge or {}).get("internet_research", {}) if isinstance(knowledge, dict) else {}, step=int(context.get("guide_step") or 1), customer_choice=requested_mode)
        context["guide_mode"] = guide.get("mode")
        context["guide_step"] = guide.get("step", 1)
        quote = None
        if requires_quote and ticket:
            quote = create_quote(company_id=company_id, customer_id=customer_id, service_id=service_id, title=ticket.get("title") or "Quote", description=message, ticket_id=ticket_id)
        response = build_response(decision=decision, ticket=ticket, knowledge=knowledge, language=language, customer_name=customer.get("full_name"))
        response_text = (response.get("response") or response.get("message") or str(response)) if isinstance(response, dict) else str(response)
        if guide.get("mode") == "OFFER_OPTIONS" and problem.get("confidence", 0) >= 0.5:
            response_text += "\n\nPuedes intentar resolverlo conmigo paso a paso, o si prefieres podemos ayudarte directamente en BiteFixes por asistencia remota o en nuestro taller. ¿Qué opción prefieres?"
        elif guide.get("mode") == "SELF_SERVICE_GUIDE":
            response_text += f"\n\nModo guía Bitey activado. Empezaremos por el paso {guide.get('step', 1)} y comprobaremos el resultado antes de continuar."
        if ticket:
            notify_event(company_id=company_id, event="ticket_created", ticket_id=ticket_id, customer_id=customer_id, service_id=service_id, intent=intent.get("intent"), message=message, channel=channel, metadata={"language": language, "ticket_type": ticket_type, "requires_quote": requires_quote, "problem_state": problem["state"], "problem_fingerprint": problem["fingerprint"], "guide_mode": guide.get("mode")})
        save_bitey_message(company_id=company_id, customer_id=customer_id, conversation_id=resolved_conversation_id, response=response_text, intent=intent.get("intent"), service_id=service_id, ticket_id=ticket_id, channel=channel)
        update_conversation_context(resolved_conversation_id, intent=intent.get("intent"), response=response_text, ticket_id=ticket_id, service_id=service_id, confidence=float(intent.get("confidence", 0) or 0), language=language, metadata={"problem_id": context.get("last_problem_id"), "problem_state": problem["state"], "guide_mode": guide.get("mode"), "guide_step": guide.get("step", 1)})
        return {"success": True, "customer_id": customer_id, "customer_name": customer.get("full_name"), "conversation_id": str(resolved_conversation_id), "channel_conversation_id": conversation_id, "language": language, "problem": problem, "problem_id": context.get("last_problem_id"), "problem_fingerprint": problem.get("fingerprint"), "guide": guide, "intent": intent.get("intent"), "confidence": float(intent.get("confidence", 0) or 0), "memory": {"used": bool(context.get("history")), "messages": len(context.get("history") or []), "problems": len(historical_problems), "scope": "customer+conversation"}, "decision": decision, "ticket": ticket, "ticket_id": ticket_id, "quote": quote, "response": response_text, "channel": channel}
    except Exception as error:
        import traceback; print("[BITEY CORE ERROR]", error); traceback.print_exc()
        return {"success": False, "error": type(error).__name__, "response": "Claro. Cuéntame un poco más sobre lo que necesitas y te ayudo.", "ticket": None, "ticket_id": None}
