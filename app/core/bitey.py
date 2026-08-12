"""
BiteFixes - Bitey Core V17
==========================

Orquestador principal de Bitey.

Flujo:

Customer
    â†“
Language Detection
    â†“
Customer
    â†“
Conversation
    â†“
Save Customer Message
    â†“
Intent Detection
    â†“
Knowledge Search
    â†“
Decision Engine
    â†“
Ticket Processing
    â†“
Quote Processing
    â†“
Response Builder
    â†“
Notification
    â†“
Save Bitey Response
    â†“
Update Conversation Context
    â†“
Final Response
"""

from typing import Any, Dict, Optional


# ============================================================
# CUSTOMER
# ============================================================

from app.services.customer_service import (
    get_or_create_customer,
)


# ============================================================
# CONVERSATION / MEMORY
# ============================================================

from app.services.conversation_service import (
    get_or_create_conversation,
)


# ============================================================
# MESSAGE SERVICE
# ============================================================

from app.services.message_service import (
    save_customer_message,
    save_bitey_message,
)


# ============================================================
# LANGUAGE
# ============================================================

from app.services.language_service import (
    detect_language,
)


# ============================================================
# INTENT
# ============================================================

from app.services.intent_service import (
    detect_intent,
)


# ============================================================
# KNOWLEDGE
# ============================================================

from app.services.knowledge_service import (
    search_knowledge,
)


# ============================================================
# DECISION ENGINE
# ============================================================

from app.services.decision_engine import (
    decision_engine,
)


# ============================================================
# TICKET
# ============================================================

from app.services.ticket_service import (
    process_ticket,
)


# ============================================================
# QUOTE
# ============================================================

from app.services.quote_service import (
    create_quote,
)


# ============================================================
# RESPONSE
# ============================================================

from app.services.response_builder import (
    build_response,
)


# ============================================================
# NOTIFICATION
# ============================================================

from app.services.notification_service import (
    notify_event,
)


# ============================================================
# CONTEXT
# ============================================================

from app.services.conversation_context_service import (
    update_conversation_context,
)


# ============================================================
# MEMORY
# ============================================================

try:

    from app.services.memory_service import (
        get_memory_context,
    )

except ImportError:

    get_memory_context = None


# ============================================================
# HELPERS
# ============================================================


def _safe_dict(value: Any) -> Dict:
    """
    Garantiza que un valor sea un dict.
    """

    if isinstance(value, dict):
        return value

    return {}


def _get_customer_id(customer: Any) -> Optional[int]:
    """
    Obtiene customer_id de forma segura.
    """

    if not customer:
        return None

    if isinstance(customer, dict):
        return customer.get("id")

    return None


def _get_customer_name(
    customer: Any,
    fallback: str = "Customer",
) -> str:
    """
    Obtiene el nombre del cliente.
    """

    if not isinstance(customer, dict):
        return fallback

    return (
        customer.get("full_name")
        or customer.get("name")
        or fallback
    )


# ============================================================
# MAIN BITEY CORE
# ============================================================


def process_message(
    company_id: int,
    message: str,
    phone: str,
    customer_name: str = "Customer",
    channel: str = "website",
):
    """
    Procesa un mensaje completo de Bitey.

    ParÃ¡metros:

        company_id:
            Empresa propietaria de la conversaciÃ³n.

        message:
            Mensaje enviado por el cliente.

        phone:
            TelÃ©fono/canal identificador del cliente.

        customer_name:
            Nombre del cliente.

        channel:
            Canal de origen.

    Retorna:

        Dict con el resultado completo del procesamiento.
    """

    print()
    print("==============================")
    print("BITEY CORE V17")
    print("==============================")

    try:

        # ====================================================
        # VALIDATION
        # ====================================================

        if not company_id:
            raise ValueError(
                "company_id is required"
            )

        if not message:
            raise ValueError(
                "message is required"
            )

        if not phone:
            raise ValueError(
                "phone is required"
            )

        message = str(message).strip()
        phone = str(phone).strip()

        # ====================================================
        # LANGUAGE DETECTION
        # ====================================================

        language = detect_language(
            message
        )

        if not language:
            language = "es"

        print(
            "[LANGUAGE]",
            language
        )

        # ====================================================
        # CUSTOMER
        # ====================================================

        customer = get_or_create_customer(
        company_id=company_id,
        phone=phone,
        name=customer_name,
    )

        customer = _safe_dict(
            customer
        )

        customer_id = _get_customer_id(
            customer
        )

        if not customer_id:
            raise ValueError(
                "Unable to obtain customer_id"
            )

        print(
            "[CUSTOMER]",
            customer_id
        )

        # ====================================================
        # CONVERSATION
        # ====================================================

        conversation = get_or_create_conversation(
            customer_id=customer_id,
            channel=channel,
        )

        conversation = _safe_dict(
            conversation
        )

        conversation_id = conversation.get(
            "id"
        )

        if not conversation_id:
            raise ValueError(
                "Unable to obtain conversation_id"
            )

        print(
            "[CONVERSATION]",
            conversation_id
        )

        # ====================================================
        # MEMORY
        # ====================================================

        memory = None

        if get_memory_context:

            try:

                memory = get_memory_context(
                    customer_id=customer_id,
                    conversation_id=conversation_id,
                )

            except TypeError:

                try:

                    memory = get_memory_context(
                        customer_id
                    )

                except Exception as memory_error:

                    print(
                        "[MEMORY WARNING]",
                        memory_error
                    )

                    memory = None

            except Exception as memory_error:

                print(
                    "[MEMORY WARNING]",
                    memory_error
                )

                memory = None

        # ====================================================
        # SAVE CUSTOMER MESSAGE
        # ====================================================

        saved_message = save_customer_message(
        company_id=company_id,
        customer_id=customer_id,
        conversation_id=conversation_id,
        message=message,
        channel=channel,
    )

        print(
            "[CUSTOMER MESSAGE SAVED]",
            saved_message
        )

        print(
            "[MESSAGE SAVED]"
        )

        # ====================================================
        # INTENT DETECTION
        # ====================================================

        intent = detect_intent(
            message,
            company_id,
        )

        intent = _safe_dict(
            intent
        )

        intent_name = intent.get(
            "intent"
        )

        confidence = intent.get(
            "confidence",
            0,
        )

        print(
            "[INTENT]",
            intent
        )

        # ====================================================
        # KNOWLEDGE SEARCH
        # ====================================================
        #
        # IMPORTANT:
        #
        # search_knowledge accepts:
        #
        # message
        # company_id
        # intent
        #
        # Do NOT send language here.
        #

        knowledge = search_knowledge(
            message=message,
            intent=intent_name,
        )

        print(
            "[KNOWLEDGE]",
            bool(knowledge)
        )

        # ====================================================
        # DECISION ENGINE
        # ====================================================

        decision = decision_engine(
            company_id,
            customer,
            message,
            intent,
            knowledge,
            memory,
        )

        decision = _safe_dict(
            decision
        )

        # ====================================================
        # FALLBACK DECISION
        # ====================================================

        if not decision:

            decision = {

                "action": "support",

                "create_ticket": True,

                "ticket_type":
                    "technical_support",

                "requires_quote": False,

                "service": None,

                "service_id": None,

                "workflow": None,

                "response":
                    "Gracias por contactar BiteFixes.",
            }

        print(
            "[DECISION]",
            decision
        )

        # ====================================================
        # SERVICE
        # ====================================================

        service_id = decision.get(
            "service_id"
        )

        service = decision.get(
            "service"
        )

        # ====================================================
        # TICKET DECISION
        # ====================================================

        create_ticket_flag = bool(
            decision.get(
                "create_ticket",
                False,
            )
        )

        ticket_type = decision.get(
            "ticket_type",
            "technical_support",
        )

        requires_quote = bool(
            decision.get(
                "requires_quote",
                False,
            )
        )

        # ====================================================
        # TICKET
        # ====================================================

        ticket = None
        ticket_id = None

        if create_ticket_flag:

            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            title = (
                service.get("name")
                if isinstance(service, dict)
                else None
            )

            if not title:
                title = (
                    intent_name
                    or "Support"
                )

            # ------------------------------------------------
            # PROCESS TICKET
            # ------------------------------------------------
            #
            # IMPORTANT:
            #
            # process_ticket() DOES NOT accept:
            #
            # create_ticket
            # requires_quote
            #
            # Those decisions belong to Bitey Core.
            #

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

            print(
                "[TICKET]",
                ticket
            )

            if ticket:

                ticket_id = ticket.get(
                    "id"
                )

        else:

            print(
                "[TICKET]",
                "Ticket creation not required"
            )

        # ====================================================
        # QUOTE
        # ====================================================

        quote = None

        if (
            requires_quote
            and ticket
        ):

            quote_title = (
                ticket.get(
                    "title"
                )
                or "Quote"
            )

            quote = create_quote(
            company_id=company_id,
            customer_id=customer_id,
            service_id=service_id,
            title=quote_title,
            description=message,
            ticket_id=ticket_id,
        )

        print(
            "[QUOTE]",
            quote
        )

        # ====================================================
        # RESPONSE BUILDER
        # ====================================================

        response = build_response(

            decision=decision,

            ticket=ticket,

            knowledge=knowledge,

            language=language,
        )

        # ----------------------------------------------------
        # RESPONSE NORMALIZATION
        # ----------------------------------------------------

        if isinstance(
            response,
            dict
        ):

            response_text = (
                response.get(
                    "response"
                )
                or response.get(
                    "message"
                )
                or str(response)
            )

        else:

            response_text = str(
                response
            )

        print(
            "[RESPONSE]",
            response
        )

        # ====================================================
        # NOTIFICATION SERVICE
        # ====================================================

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

                    "confidence":
                        confidence,

                    "language":
                        language,

                    "quote_id":
                        (
                            quote.get("id")
                            if quote
                            else None
                        ),

                    "ticket_type":
                        ticket_type,

                    "requires_quote":
                        requires_quote,
                },
            )

            print(
                "[NOTIFICATION SENT]"
            )

        # ====================================================
        # SAVE BITEY MESSAGE
        # ====================================================

        save_bitey_message(
        company_id=company_id,
        customer_id=customer_id,

            conversation_id=conversation_id,

            response=response_text,

            intent=intent_name,

            confidence=confidence,

            service_id=service_id,

            ticket_id=ticket_id,

            channel=channel,
        )

        print(
            "[BITEY MESSAGE SAVED]"
        )

        # ====================================================
        # UPDATE CONVERSATION CONTEXT
        # ====================================================

        update_conversation_context(

            conversation_id,

            intent=intent_name,

            response=response_text,

            ticket_id=ticket_id,
        )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return {

            "success":
                True,

            "customer_id":
                customer_id,

            "conversation_id":
                conversation_id,

            "language":
                language,

            "intent":
                intent_name,

            "confidence":
                confidence,

            "knowledge":
                knowledge,

            "knowledge_found":
                bool(knowledge),

            "decision":
                decision,

            "ticket":
                ticket,

            "ticket_id":
                ticket_id,

            "quote":
                quote,

            "response":
                response_text,

            "channel":
                channel,
        }

    # ========================================================
    # GLOBAL ERROR HANDLER
    # ========================================================

    except Exception as error:

        import traceback

        print(
            "[BITEY CORE ERROR]",
            error
        )

        traceback.print_exc()

        return {

            "success":
                False,

            "error":
                str(error),

            "response":
                "Error processing request.",
        }








