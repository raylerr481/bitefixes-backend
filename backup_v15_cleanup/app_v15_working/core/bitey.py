"""
=====================================================
BITEY CORE V15
=====================================================

Central AI Orchestration Engine

Flow

Customer
↓

Language Detection
↓

Conversation

↓

Customer Context

↓

Save Customer Message

↓

Intent Detection

↓

Knowledge Search

↓

Decision Engine

↓

Workflow

↓

Ticket

↓

Notification

↓

Response Builder

↓

Save AI Message

↓

Return
"""

from app.services.customer_service import get_or_create_customer

from app.services.conversation_service import (
    get_or_create_conversation,
    update_conversation_context
)

from app.services.context_service import (
    build_customer_context
)

from app.services.message_service import (
    save_customer_message,
    save_bitey_message
)

from app.services.intent_service import (
    detect_intent
)

from app.services.knowledge_service import (
    search_knowledge
)

from app.services.ticket_service import (
    process_ticket
)

from app.services.notification_service import (
    notify_event
)

from app.core.decision_engine import (
    decision_engine
)

from app.services.language_service import (
    detect_language
)

from app.services.response_builder import (
    build_response
)


def process_message(
    company_id: int,
    message: str,
    whatsapp: str,
    customer_name: str,
    channel: str = "website"
):

    print("\n==============================")
    print("BITEY CORE V15")
    print("==============================")
    print(message)

    try:

        # ======================================
        # LANGUAGE
        # ======================================

        language = detect_language(message)

        print("[LANGUAGE]", language)

        # ======================================
        # CUSTOMER
        # ======================================

        customer = get_or_create_customer(
            company_id,
            whatsapp,
            customer_name
        )

        customer_id = customer["id"]

        print("[CUSTOMER]", customer_id)

        # ======================================
        # CONVERSATION
        # ======================================

        conversation = get_or_create_conversation(
            customer_id,
            channel
        )

        conversation_id = conversation["id"]

        print("[CONVERSATION]", conversation_id)

        # ======================================
        # MEMORY
        # ======================================

        context = build_customer_context(
            customer_id,
            company_id
        )

        memory = context.get(
            "summary",
            {}
        )

        # ======================================
        # SAVE CUSTOMER MESSAGE
        # ======================================

        save_customer_message(

            company_id=company_id,

            customer_id=customer_id,

            conversation_id=conversation_id,

            message=message,

            channel=channel

        )

        print("[CUSTOMER MESSAGE SAVED]")

        # ======================================
        # INTENT
        # ======================================

        intent = detect_intent(
            message,
            company_id
        )

        intent_name = intent.get("intent")

        confidence = intent.get(
            "confidence",
            0
        )

        print("[INTENT]", intent)

        # ======================================
        # KNOWLEDGE
        # ======================================

        knowledge = search_knowledge(
            message,
            company_id
        )

        print("[KNOWLEDGE]", bool(knowledge))

        # ======================================
        # DECISION
        # ======================================

        decision = decision_engine(

            company_id,

            customer,

            message,

            intent,

            knowledge,

            memory

        )

        if not decision:

            decision = {

                "action": "support",

                "create_ticket": True,

                "ticket_type": "technical_support",

                "response": ""

            }

        print("[DECISION]", decision)

        service_id = decision.get(
            "service_id"
        )

        workflow = decision.get(
            "workflow"
        )

        # ======================================
        # TICKET
        # ======================================

        ticket = process_ticket(

            company_id=company_id,

            customer_id=customer_id,

            service_id=service_id,

            intent=intent_name,

            description=message,

            title=decision.get(
                "action",
                "support"
            ),

            channel=channel,

            language=language,

            ticket_type=decision.get(
                "ticket_type",
                "technical_support"
            ),

            create_ticket=decision.get(
                "create_ticket",
                False
            )

        )

        print("[TICKET]", ticket)

        ticket_id = None

        if ticket:

            ticket_id = ticket.get("id")

        # ======================================
        # RESPONSE BUILDER
        # ======================================

        response = build_response(

            knowledge=knowledge,

            language=language,

            ticket=ticket

        )

        print("[RESPONSE BUILDER OK]")

        # ======================================
        # NOTIFICATION
        # ======================================

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

                    "ticket_code": ticket.get(
                        "ticket_code"
                    )

                }

            )

        # ======================================
        # SAVE AI MESSAGE
        # ======================================

        save_bitey_message(

            company_id=company_id,

            customer_id=customer_id,

            conversation_id=conversation_id,

            response=response,

            intent=intent_name,

            confidence=confidence,

            service_id=service_id,

            ticket_id=ticket_id,

            channel=channel

        )

        print("[BITEY MESSAGE SAVED]")

        # ======================================
        # UPDATE CONVERSATION
        # ======================================

        update_conversation_context(

            conversation_id,

            intent=intent_name,

            response=response,

            ticket_id=ticket_id

        )

        # ======================================
        # RETURN
        # ======================================

        return {

            "success": True,

            "customer_id": customer_id,

            "conversation_id": conversation_id,

            "language": language,

            "intent": intent_name,

            "confidence": confidence,

            "knowledge": knowledge,

            "knowledge_found": bool(knowledge),

            "decision": decision,

            "workflow": workflow,

            "ticket": ticket,

            "ticket_id": ticket_id,

            "response": response

        }

    except Exception as error:

        import traceback

        print("[BITEY CORE ERROR]", error)

        traceback.print_exc()

        return {

            "success": False,

            "error": str(error),

            "response": "Erro ao processar sua solicitação."

        }