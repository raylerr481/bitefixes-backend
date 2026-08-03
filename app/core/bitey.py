"""
Bitey Core AI Engine V12
--------------------------------

Central orchestration layer.

Flow

Customer
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
Ticket Service
    ↓
Notification Service
    ↓
Save Bitey Response
    ↓
Return Result
"""

from app.services.customer_service import (
    get_or_create_customer
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


def process_message(
    company_id: int,
    message: str,
    whatsapp: str,
    customer_name: str,
    channel: str = "website"
):

    print("\n==============================")
    print("BITEY CORE V12")
    print("==============================")
    print(message)
    print("==============================")

    try:

        # ==========================================
        # CUSTOMER
        # ==========================================

        customer = get_or_create_customer(
            company_id,
            whatsapp,
            customer_name
        )

        customer_id = customer["id"]

        print(
            "[CUSTOMER]",
            customer_id
        )

        # ==========================================
        # MEMORY
        # ==========================================

        context = build_customer_context(
            customer_id,
            company_id
        )

        memory = context.get(
            "summary",
            {}
        )

        print(
            "[MEMORY]",
            memory
        )

        # ==========================================
        # SAVE CUSTOMER MESSAGE
        # ==========================================

        save_customer_message(

            company_id=company_id,

            customer_id=customer_id,

            conversation_id=None,

            message=message,

            channel=channel

        )

        # ==========================================
        # INTENT
        # ==========================================

        intent = detect_intent(

            message,

            company_id

        )

        print(
            "[INTENT]",
            intent
        )

        intent_name = intent.get(
            "intent"
        )

        confidence = intent.get(
            "confidence",
            0
        )

        # ==========================================
        # KNOWLEDGE
        # ==========================================

        knowledge = search_knowledge(

            message,

            company_id

        )

        print(
            "[KNOWLEDGE]",
            bool(knowledge)
        )

        # ==========================================
        # DECISION ENGINE
        # ==========================================

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

                "ticket_type": "support",

                "response":
                    "Recebemos sua solicitação."

            }

        print(
            "[DECISION]",
            decision
        )

        # ==========================================
        # SERVICE
        # ==========================================

        service = decision.get(
            "service"
        )

        service_id = decision.get(
            "service_id"
        )

        # ==========================================
        # TICKET SERVICE
        # ==========================================

        ticket = process_ticket(

            company_id=company_id,

            customer_id=customer_id,

            service_id=service_id,

            intent=intent_name,

            description=message,

            title=decision.get(
                "action",
                "workflow"
            ),

            channel=channel,

            ticket_type=decision.get(
                "ticket_type",
                "support"
            ),

            create_ticket=decision.get(
                "create_ticket",
                True
            )

        )

        print(
            "[TICKET]",
            ticket
        )

        # ==========================================
        # NOTIFICATION
        # ==========================================

        if ticket:

            notify_event(

                company_id=company_id,

                event="ticket_created",

                customer_id=customer_id,

                ticket_id=ticket.get("id"),

                service_id=service_id,

                intent=intent_name,

                message=message,

                channel=channel,

                metadata=decision.get(
                    "metadata"
                )

            )

        # ==========================================
        # RESPONSE
        # ==========================================

        response = decision.get(
            "response"
        )

        if not response:

            response = (
                "Obrigado por contactar Bitey. "
                "Sua solicitação foi registrada."
            )

        # (Continúa en la Parte 2)
                # ==========================================
        # SAVE BITEY RESPONSE
        # ==========================================

        save_bitey_message(

            company_id=company_id,

            customer_id=customer_id,

            conversation_id=None,

            response=response,

            intent=intent_name,

            confidence=confidence,

            service_id=service_id,

            ticket_id=(
                ticket.get("id")
                if ticket
                else None
            ),

            channel=channel

        )

        # ==========================================
        # RESULT
        # ==========================================

        result = {

            "success": True,

            "customer_id": customer_id,

            "memory": memory,

            "intent": intent,

            "knowledge": knowledge,

            "knowledge_found": bool(
                knowledge
            ),

            "decision": decision,

            "service": service,

            "ticket": ticket,

            "response": response

        }

        print(
            "[BITEY RESULT]",
            result
        )

        return result

    except Exception as error:

        print(
            "[BITEY CORE ERROR]",
            repr(error)
        )

        return {

            "success": False,

            "customer_id": None,

            "memory": {},

            "intent": None,

            "knowledge": None,

            "knowledge_found": False,

            "decision": None,

            "service": None,

            "ticket": None,

            "response": (
                "Ocorreu um erro ao processar "
                "sua solicitação."
            ),

            "error": str(error)

        }