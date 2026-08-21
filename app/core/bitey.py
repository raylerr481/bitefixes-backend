"""BiteFixes - Bitey Core V22 cognitive learning runtime."""

from typing import Any, Dict, Optional
from app.services.customer_service import get_or_create_customer
from app.services.conversation_service import get_or_create_conversation
from app.services.message_service import save_customer_message, save_bitey_message
from app.services.language_service import detect_language
from app.services.intent_service import detect_intent
from app.services.knowledge_service import search_knowledge
from app.services.decision_engine import decision_engine
from app.services.ticket_service import process_ticket
from app.services.quote_service import create_quote
from app.services.response_builder import build_response
from app.services.notification_service import notify_event
from app.services.conversation_context_service import update_conversation_context
from app.services.bitey_learning_engine import build_learning_context, evaluate_external_result, record_learning_candidate

try:
    from app.services.memory_service import get_memory_context
except ImportError:
    get_memory_context = None
try:
    from app.services.integration_orchestrator import prepare_openapi_tools
except ImportError:
    prepare_openapi_tools = None
try:
    from app.ai.consultation_service import consult_if_valuable
except ImportError:
    consult_if_valuable = None
try:
    from app.ai.comparative_engine import compare_answers
except ImportError:
    compare_answers = None
try:
    from app.ai.comparison_audit import record_comparison
except ImportError:
    record_comparison = None


def _safe_dict(value: Any) -> Dict:
    return value if isinstance(value, dict) else {}

def _get_customer_id(customer: Any) -> Optional[int]:
    return customer.get("id") if isinstance(customer, dict) else None

def _normalize_language_preference(value: Optional[str]) -> Optional[str]:
    if not value: return None
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"pt", "pt-br"}: return "pt-BR"
    if normalized == "es": return "es"
    if normalized == "en": return "en"
    return None

def _prepare_external_integration(decision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    request = decision.get("external_integration")
    if not isinstance(request, dict) or not prepare_openapi_tools: return None
    document = request.get("openapi_document")
    if not isinstance(document, dict): return {"status":"rejected","reason":"missing_openapi_document","executed":False}
    try: return prepare_openapi_tools(document)
    except Exception as error: return {"status":"rejected","reason":str(error),"executed":False}

def process_message(company_id: int, message: str, phone: str, email: str = "", customer_name: str = "Customer",
                    last_name: str = "", channel: str = "website", conversation_id: Optional[str] = None,
                    language_preference: str = "auto", page_context: dict | None = None,
                    service_context: dict | None = None):
    """Process a message: enterprise context -> external reasoning -> evaluation -> learning."""
    try:
        if not company_id: raise ValueError("company_id is required")
        if not message: raise ValueError("message is required")
        message = str(message).strip()
        supplied_phone, supplied_email = str(phone or "").strip(), str(email or "").strip()
        supplied_name = " ".join(p for p in [str(customer_name or "").strip(), str(last_name or "").strip()] if p) or "Customer"
        explicit_language = _normalize_language_preference(language_preference)
        if language_preference not in (None, "", "auto") and not explicit_language: raise ValueError("Unsupported language_preference")
        detected_language = detect_language(message) or "es"
        language, language_source = explicit_language or detected_language, ("explicit" if explicit_language else "detected")
        identity_phone = supplied_phone if supplied_phone and supplied_phone.lower() not in {"web","unknown"} else (f"web:{conversation_id}" if conversation_id else "web")
        customer = _safe_dict(get_or_create_customer(company_id=company_id, phone=identity_phone, email=supplied_email, name=supplied_name))
        customer_id = _get_customer_id(customer)
        if not customer_id: raise ValueError("Unable to obtain customer_id")
        conversation = _safe_dict(get_or_create_conversation(customer_id=customer_id, channel=channel))
        resolved_conversation_id = conversation.get("id")
        if not resolved_conversation_id: raise ValueError("Unable to obtain conversation_id")
        memory = None
        if get_memory_context:
            try: memory = get_memory_context(customer_id=customer_id, conversation_id=resolved_conversation_id)
            except Exception as error: print("[MEMORY WARNING]", error)
        save_customer_message(company_id=company_id, customer_id=customer_id, conversation_id=resolved_conversation_id, message=message, channel=channel)
        intent = _safe_dict(detect_intent(message, company_id))
        intent_name, confidence = intent.get("intent"), intent.get("confidence", 0)
        knowledge = search_knowledge(message=message, company_id=company_id, intent=intent_name, language=language)
        decision = _safe_dict(decision_engine(company_id, customer, message, intent, knowledge, memory, language)) or {"action":"conversation","create_ticket":False,"requires_quote":False,"response":"Gracias por contactar BiteFixes."}

        # The enterprise context is prepared before external reasoning.
        learning_context = build_learning_context(company_id=company_id, message=message, page_context=page_context,
                                                  service_context=service_context, memory=memory)
        decision["bitey_context"] = learning_context

        consultation = {"used": False, "reason": "unavailable"}
        if consult_if_valuable:
            try:
                consultation = consult_if_valuable(company_id=company_id, message=message, language=language,
                    intent=intent, context={"enterprise_context": learning_context, "core_confidence": float(confidence or 0),
                                            "knowledge": knowledge, "service_context": service_context or {}},
                    conversation_id=resolved_conversation_id)
            except Exception as error:
                print("[AI CONSULTATION WARNING]", error); consultation = {"used":False,"reason":"consultation_error"}
        decision["ai_consultation"] = consultation

        comparison = {"status":"unavailable"}
        if compare_answers:
            candidates = []
            if decision.get("response"): candidates.append({"source":"core","answer":decision["response"],"intent":intent_name,"authority":1.0,"safety":1.0})
            if isinstance(knowledge, dict) and knowledge.get("answer"): candidates.append({"source":"knowledge","answer":knowledge["answer"],"intent":knowledge.get("intent") or intent_name,"authority":1.0,"safety":1.0})
            for suggestion in consultation.get("suggestions", []) if isinstance(consultation, dict) else []:
                if suggestion.get("answer"): candidates.append({"source":"external","provider":suggestion.get("provider"),"answer":suggestion["answer"],"intent":suggestion.get("intent") or intent_name,"authority":0.45,"safety":0.85})
            comparison = compare_answers(message=message, intent=intent_name, core_confidence=float(confidence or 0), candidates=candidates)
            decision["comparative_evaluation"] = comparison
            if record_comparison:
                try: record_comparison(company_id=company_id, conversation_id=resolved_conversation_id, message=message, intent=intent_name, core_confidence=float(confidence or 0), consultation_used=bool(consultation.get("used")), comparison=comparison)
                except Exception as error: print("[AI COMPARISON AUDIT WARNING]", error)
        decision["response_source"] = decision.get("response_source", "core")

        # Learn from the external interaction without replacing the external AI's role.
        suggestions = consultation.get("suggestions", []) if isinstance(consultation, dict) else []
        learning_events = []
        for suggestion in suggestions:
            answer = str(suggestion.get("answer") or "").strip()
            if not answer: continue
            evaluation = evaluate_external_result(response=answer, context=learning_context,
                                                   service=(service_context or {}).get("service") if isinstance(service_context, dict) else intent_name)
            learning_events.append(evaluation)
            if evaluation["score"] >= 0.70:
                record_learning_candidate(company_id=company_id, kind="method", title=f"{intent_name or 'conversation'} reasoning pattern",
                                          payload={"message":message,"answer":answer,"context":learning_context,"evaluation":evaluation,"provider":suggestion.get("provider")},
                                          confidence=evaluation["score"], source="external_ai")

        service_id = decision.get("service_id")
        service = decision.get("service")
        ticket = None
        ticket_id = None
        # Existing decision engine remains responsible for action authorization.
        if bool(decision.get("create_ticket", False)):
            title = service.get("name") if isinstance(service, dict) else None
            title = title or intent_name or "Support"
            ticket = process_ticket(company_id=company_id, customer_id=customer_id, service_id=service_id, intent=intent_name, description=message, title=title, language=language, channel=channel, ticket_type=decision.get("ticket_type","technical_support"))
            if ticket: ticket_id = ticket.get("id")
        quote = None
        if bool(decision.get("requires_quote", False)) and ticket:
            quote = create_quote(company_id=company_id, customer_id=customer_id, service_id=service_id, title=ticket.get("title") or "Quote", description=message, ticket_id=ticket_id)
        response = build_response(decision=decision, ticket=ticket, knowledge=knowledge, language=language, customer_name=customer.get("full_name"))
        response_text = (response.get("response") or response.get("message") or str(response)) if isinstance(response, dict) else str(response)
        if ticket: notify_event(company_id=company_id,event="ticket_created",ticket_id=ticket_id,customer_id=customer_id,service_id=service_id,intent=intent_name,message=message,channel=channel,metadata={"confidence":confidence,"language":language})
        save_bitey_message(company_id=company_id,customer_id=customer_id,conversation_id=resolved_conversation_id,response=response_text,intent=intent_name,confidence=confidence,service_id=service_id,ticket_id=ticket_id,channel=channel)
        update_conversation_context(resolved_conversation_id,intent=intent_name,response=response_text,ticket_id=ticket_id)
        return {"success":True,"customer_id":customer_id,"customer_name":customer.get("full_name"),"conversation_id":str(resolved_conversation_id),"channel_conversation_id":conversation_id,
                "language":language,"language_source":language_source,"intent":intent_name,"confidence":confidence,"knowledge":knowledge,"knowledge_found":bool(knowledge),
                "memory":{"used":bool(memory),"scope":"customer"},"bitey_context":learning_context,"ai_consultation":consultation,"learning_events":learning_events,
                "comparative_evaluation":decision.get("comparative_evaluation"),"response_source":decision.get("response_source","core"),"decision":decision,
                "ticket":ticket,"ticket_id":ticket_id,"quote":quote,"response":response_text,"channel":channel}
    except Exception as error:
        import traceback; print("[BITEY CORE ERROR]",error); traceback.print_exc()
        return {"success":False,"error":str(error),"response":"Error processing request."}
