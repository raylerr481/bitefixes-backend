"""BiteFixes - Bitey Core V19."""

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

try:
    from app.services.memory_service import get_memory_context
except ImportError:
    get_memory_context = None

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
    if normalized in {"pt", "pt-br"}:
        return "pt-BR"
    if normalized == "es":
        return "es"
    if normalized == "en":
        return "en"
    return None


def _prepare_external_integration(decision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    request = decision.get("external_integration")
    if not isinstance(request, dict) or not prepare_openapi_tools:
        return None
    document = request.get("openapi_document")
    if not isinstance(document, dict):
        return {"status": "rejected", "reason": "missing_openapi_document", "executed": False}
    try:
        return prepare_openapi_tools(document)
    except Exception as error:
        return {"status": "rejected", "reason": str(error), "executed": False}


def process_message(
    company_id: int,
    message: str,
    phone: str,
    customer_name: str = "Customer",
    channel: str = "website",
    conversation_id: Optional[str] = None,
    language_preference: str = "auto",
):
    """Process a Bitey message with explicit-or-detected language priority."""
    try:
        if not company_id:
            raise ValueError("company_id is required")
        if not message:
            raise ValueError("message is required")

        message = str(message).strip()
        supplied_phone = str(phone or "").strip()
        supplied_name = str(customer_name or "").strip() or "Customer"

        explicit_language = _normalize_language_preference(language_preference)
        if language_preference not in (None, "", "auto") and not explicit_language:
            raise ValueError("Unsupported language_preference. Use auto, pt-BR, es or en.")

        detected_language = detect_language(message) or "es"
        language = explicit_language or detected_language
        language_source = "explicit" if explicit_language else "detected"

        # Website visitors without a phone still need a stable customer identity.
        # Use the browser conversation id instead of the shared legacy value "web".
        identity_phone = supplied_phone
        if not identity_phone or identity_phone.lower() in {"web", "unknown"}:
            identity_phone = f"web:{conversation_id}" if conversation_id else "web"

        customer = _safe_dict(
            get_or_create_customer(
                company_id=company_id,
                phone=identity_phone,
                name=supplied_name,
            )
        )
        customer_id = _get_customer_id(customer)
        if not customer_id:
            raise ValueError("Unable to obtain customer_id")

        conversation = _safe_dict(
            get_or_create_conversation(customer_id=customer_id, channel=channel)
        )
        resolved_conversation_id = conversation.get("id")
        if not resolved_conversation_id:
            raise ValueError("Unable to obtain conversation_id")

        memory = None
        if get_memory_context:
            try:
                memory = get_memory_context(customer_id=customer_id, conversation_id=resolved_conversation_id)
            except TypeError:
                try:
                    memory = get_memory_context(customer_id)
                except Exception as error:
                    print("[MEMORY WARNING]", error)
            except Exception as error:
                print("[MEMORY WARNING]", error)

        save_customer_message(
            company_id=company_id,
            customer_id=customer_id,
            conversation_id=resolved_conversation_id,
            message=message,
            channel=channel,
        )

        intent = _safe_dict(detect_intent(message, company_id))
        intent_name = intent.get("intent")
        confidence = intent.get("confidence", 0)
        knowledge = search_knowledge(message=message, company_id=company_id, intent=intent_name)
        decision = _safe_dict(
            decision_engine(company_id, customer, message, intent, knowledge, memory, language)
        )

        if not decision:
            decision = {
                "action": "conversation",
                "create_ticket": False,
                "ticket_type": None,
                "requires_quote": False,
                "service": None,
                "service_id": None,
                "workflow": None,
                "response": "Gracias por contactar BiteFixes.",
            }

        external_integration = _prepare_external_integration(decision)
        if external_integration is not None:
            decision["external_integration"] = external_integration

        # A workflow must explicitly succeed before it can authorize ticket creation.
        workflow_result = decision.get("workflow_result")
        if decision.get("action") == "workflow":
            workflow_result = workflow_result or {}
            if not workflow_result.get("success", False):
                decision["create_ticket"] = False
                decision["requires_quote"] = False
                decision["response"] = workflow_result.get("response") or decision.get("response") or "Voy a ayudarte a completar el diagnóstico antes de registrar una solicitud."

        service_id = decision.get("service_id")
        service = decision.get("service")
        create_ticket_flag = bool(decision.get("create_ticket", False))
        ticket_type = decision.get("ticket_type", "technical_support")
        requires_quote = bool(decision.get("requires_quote", False))
        ticket = None
        ticket_id = None

        if create_ticket_flag:
            title = service.get("name") if isinstance(service, dict) else None
            title = title or intent_name or "Support"
            ticket = process_ticket(
                company_id=company_id,
                customer_id=customer_id,
                service_id=service_id,
                intent=intent_name,
                description=message,
                title=title,
                language=language,
                channel=channel,
                ticket_type=ticket_type,
            )
            if ticket:
                ticket_id = ticket.get("id")

        quote = None
        if requires_quote and ticket:
            quote = create_quote(
                company_id=company_id,
                customer_id=customer_id,
                service_id=service_id,
                title=ticket.get("title") or "Quote",
                description=message,
                ticket_id=ticket_id,
            )

        response = build_response(
            decision=decision,
            ticket=ticket,
            knowledge=knowledge,
            language=language,
            customer_name=customer.get("full_name"),
        )
        response_text = (
            response.get("response") or response.get("message") or str(response)
            if isinstance(response, dict)
            else str(response)
        )

        if ticket:
            notify_event(
                company_id=company_id,
                event="ticket_created",
                ticket_id=ticket_id,
                customer_id=customer_id,
                service_id=service_id,
                intent=intent_name,
                message=message,
                channel=channel,
                metadata={
                    "confidence": confidence,
                    "language": language,
                    "language_source": language_source,
                    "quote_id": quote.get("id") if quote else None,
                    "ticket_type": ticket_type,
                    "requires_quote": requires_quote,
                },
            )

        save_bitey_message(
            company_id=company_id,
            customer_id=customer_id,
            conversation_id=resolved_conversation_id,
            response=response_text,
            intent=intent_name,
            confidence=confidence,
            service_id=service_id,
            ticket_id=ticket_id,
            channel=channel,
        )
        update_conversation_context(
            resolved_conversation_id,
            intent=intent_name,
            response=response_text,
            ticket_id=ticket_id,
        )

        return {
            "success": True,
            "customer_id": customer_id,
            "customer_name": customer.get("full_name"),
            "conversation_id": str(resolved_conversation_id),
            "channel_conversation_id": conversation_id,
            "language": language,
            "language_source": language_source,
            "intent": intent_name,
            "confidence": confidence,
            "knowledge": knowledge,
            "knowledge_found": bool(knowledge),
            "decision": decision,
            "ticket": ticket,
            "ticket_id": ticket_id,
            "quote": quote,
            "response": response_text,
            "channel": channel,
        }
    except Exception as error:
        import traceback
        print("[BITEY CORE ERROR]", error)
        traceback.print_exc()
        return {"success": False, "error": str(error), "response": "Error processing request."}
