"""BiteFixes - Bitey Core V24."""
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
from app.services.problem_identity_service import classify_problem

try:
    from app.services.memory_service import get_memory_context
except ImportError:
    get_memory_context = None
try:
    from app.services.memory_service import get_customer_memory
except ImportError:
    get_customer_memory = None
try:
    from app.services.integration_orchestrator import prepare_openapi_tools
except ImportError:
    prepare_openapi_tools = None


def _safe_dict(value: Any) -> Dict:
    return value if isinstance(value, dict) else {}


def _get_customer_id(customer: Any) -> Optional[int]:
    return customer.get("id") if isinstance(customer, dict) else None


def _normalize_language_preference(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = value.strip().lower().replace("_", "-")
    return {"pt": "pt-BR", "pt-br": "pt-BR", "es": "es", "en": "en"}.get(normalized)


def _is_greeting(message: str) -> bool:
    return " ".join(str(message or "").lower().strip().split()) in {"hola", "hello", "hi", "hey", "oi", "ola", "buenas", "buenos dias", "buenas tardes", "buenas noches"}


def _load_memory(customer_id: int, company_id: int, conversation_id: str) -> Dict[str, Any]:
    if get_memory_context:
        try:
            result = get_memory_context(customer_id=customer_id, conversation_id=conversation_id)
            if isinstance(result, dict): return result
        except TypeError:
            try:
                result = get_memory_context(customer_id)
                if isinstance(result, dict): return result
            except Exception: pass
        except Exception: pass
    if get_customer_memory:
        try:
            result = get_customer_memory(company_id=company_id, customer_id=customer_id, limit=20)
            return result if isinstance(result, dict) else {}
        except Exception: pass
    return {}


def _build_context(conversation_context: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
    context = dict(conversation_context or {})
    context["memory"] = memory
    context["history"] = memory.get("history") or []
    context["last_intent"] = memory.get("last_intent") or context.get("last_intent") or context.get("intent")
    context["last_service"] = memory.get("last_service") or context.get("last_service") or context.get("service_id")
    context["last_ticket"] = memory.get("last_ticket") or context.get("last_ticket") or context.get("ticket_id")
    context["last_confidence"] = memory.get("last_confidence") or context.get("last_confidence") or 0.0
    context["conversation_id"] = context.get("id")
    return context


def process_message(company_id: int, message: str, phone: str, email: str = "", customer_name: str = "Customer", last_name: str = "", channel: str = "website", conversation_id: Optional[str] = None, language_preference: str = "auto", external_id: str = ""):
    try:
        if not company_id or not message: raise ValueError("company_id and message are required")
        message = str(message).strip()
        supplied_phone, supplied_email = str(phone or "").strip(), str(email or "").strip()
        supplied_name = " ".join(part for part in [str(customer_name or "").strip(), str(last_name or "").strip()] if part) or "Customer"
        explicit_language = _normalize_language_preference(language_preference)
        if language_preference not in (None, "", "auto") and not explicit_language: raise ValueError("Unsupported language_preference")
        language = explicit_language or detect_language(message) or "es"

        # Identity is resolved before problem/intent analysis.
        identity_phone = supplied_phone
        if not identity_phone or identity_phone.lower() in {"web", "unknown"}:
            identity_phone = f"web:{conversation_id}" if conversation_id else "web"
        customer = _safe_dict(get_or_create_customer(company_id=company_id, phone=identity_phone, email=supplied_email, name=customer_name or "Customer", last_name=last_name, channel=channel, external_id=external_id))
        customer_id = _get_customer_id(customer)
        if not customer_id: raise ValueError("Unable to obtain customer_id")

        conversation = _safe_dict(get_or_create_conversation(customer_id=customer_id, channel=channel, conversation_id=conversation_id))
        resolved_conversation_id = conversation.get("id")
        if not resolved_conversation_id: raise ValueError("Unable to obtain conversation_id")
        conversation_context = _safe_dict(get_conversation(resolved_conversation_id, customer_id=customer_id))
        memory = _load_memory(customer_id, company_id, str(resolved_conversation_id))
        context = _build_context(conversation_context, memory)
        context.update({"company_id": company_id, "language": language})
        save_customer_message(company_id=company_id, customer_id=customer_id, conversation_id=resolved_conversation_id, message=message, channel=channel)

        intent = _safe_dict(detect_intent(message, company_id, context=context))
        active_intent = context.get("last_intent")
        # Problem identity is evaluated BEFORE inheriting the previous intent.
        problem = classify_problem(message=message, current_intent=intent.get("intent"), active_intent=active_intent, active_problem=context.get("last_problem"), active_device=context.get("last_device"))
        context["problem_state"] = problem["state"]
        context["problem_is_new"] = problem["is_new"]
        if problem.get("device"): context["last_device"] = problem["device"]

        # Never inherit an old intent when this is a genuinely new problem.
        if not intent.get("intent") and active_intent and not problem["is_new"] and not _is_greeting(message):
            intent = {"intent": active_intent, "confidence": max(0.70, float(context.get("last_confidence") or 0.0)), "context_inherited": True, "context_source": "active_conversation"}
        elif problem["is_new"]:
            context["last_intent"] = None
            context["last_service"] = None
            context["last_ticket"] = None

        knowledge = search_knowledge(message=message, company_id=company_id, intent=intent.get("intent"), language=language)
        decision = _safe_dict(ai_first_decision(company_id=company_id, customer=customer, message=message, intent=intent, knowledge=knowledge, memory={**memory, "conversation_id": resolved_conversation_id, "history": context.get("history", []), "problem_state": problem["state"]}, language=language, business_context=context))
        if not decision:
            decision = {"action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None, "service": None, "service_id": None, "response": "Claro. Cuéntame un poco más sobre lo que necesitas.", "metadata": {"architecture": "ai_first_v24", "fallback": "safe_conversation"}}

        # A new problem cannot silently reuse the previous ticket/service.
        if problem["is_new"]:
            decision["ticket_id"] = None
            decision["service_id"] = decision.get("service_id") if intent.get("intent") else None
            if not intent.get("intent"): decision["create_ticket"] = False

        service_id = decision.get("service_id")
        service = decision.get("service")
        create_ticket_flag = bool(decision.get("create_ticket", False))
        requires_quote = bool(decision.get("requires_quote", False))
        ticket_type = decision.get("ticket_type", "technical_support")
        ticket = None
        ticket_id = None
        if create_ticket_flag:
            title = service.get("name") if isinstance(service, dict) else None
            title = title or intent.get("intent") or "Support"
            ticket = process_ticket(company_id=company_id, customer_id=customer_id, service_id=service_id, intent=intent.get("intent"), description=message, title=title, language=language, channel=channel, ticket_type=ticket_type)
            ticket_id = ticket.get("id") if ticket else None
        quote = None
        if requires_quote and ticket:
            quote = create_quote(company_id=company_id, customer_id=customer_id, service_id=service_id, title=ticket.get("title") or "Quote", description=message, ticket_id=ticket_id)
        response = build_response(decision=decision, ticket=ticket, knowledge=knowledge, language=language, customer_name=customer.get("full_name"))
        response_text = (response.get("response") or response.get("message") or str(response)) if isinstance(response, dict) else str(response)
        if ticket:
            notify_event(company_id=company_id, event="ticket_created", ticket_id=ticket_id, customer_id=customer_id, service_id=service_id, intent=intent.get("intent"), message=message, channel=channel, metadata={"language": language, "ticket_type": ticket_type, "requires_quote": requires_quote, "problem_state": problem["state"]})
        save_bitey_message(company_id=company_id, customer_id=customer_id, conversation_id=resolved_conversation_id, response=response_text, intent=intent.get("intent"), service_id=service_id, ticket_id=ticket_id, channel=channel)
        update_conversation_context(resolved_conversation_id, intent=intent.get("intent"), response=response_text, ticket_id=ticket_id, service_id=service_id, language=language)
        return {"success": True, "customer_id": customer_id, "customer_name": customer.get("full_name"), "conversation_id": str(resolved_conversation_id), "channel_conversation_id": conversation_id, "language": language, "problem": problem, "intent": intent.get("intent"), "confidence": float(intent.get("confidence", 0) or 0), "memory": {"used": bool(context.get("history")), "messages": len(context.get("history") or []), "scope": "conversation"}, "decision": decision, "ticket": ticket, "ticket_id": ticket_id, "quote": quote, "response": response_text, "channel": channel}
    except Exception as error:
        import traceback
        print("[BITEY CORE ERROR]", error)
        traceback.print_exc()
        return {"success": False, "error": type(error).__name__, "response": "Claro. Cuéntame un poco más sobre lo que necesitas y te ayudo.", "ticket": None, "ticket_id": None}
