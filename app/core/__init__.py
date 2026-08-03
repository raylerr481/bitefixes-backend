"""
BiteFixes Bitey AI Core V3

Central orchestration engine.

Flow:

Customer
Conversation
Context
Intent
Knowledge
Service
Reasoning
Decision
Ticket
Response
Memory
AI Logs
"""


from app.services.customer_service import (
    get_or_create_customer
)

from app.services.conversation_service import (
    get_or_create_conversation,
    update_conversation
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

from app.services.service_resolver import (
    resolve_service
)

from app.services.ticket_service import (
    create_ticket,
    find_open_ticket
)

from app.core.context_engine import (
    build_context
)

from app.core.reasoning_engine import (
    analyze_context
)


from app.core.response_engine import (
    generate_response
)



def process_message(
    company_id,
    message,
    whatsapp,
    customer_name="Customer",
    channel="website"
):

    try:


        # ==========================
        # CUSTOMER
        # ==========================

        customer = get_or_create_customer(
            company_id,
            whatsapp,
            customer_name
        )


        customer_id = customer["id"]



        # ==========================
        # CONVERSATION
        # ==========================

        conversation = get_or_create_conversation(
            customer_id,
            channel
        )

        conversation_id = conversation["id"]



        # ==========================
        # CONTEXT
        # ==========================

        context = build_context(
            customer_id,
            message
        )



        # ==========================
        # SAVE CUSTOMER MESSAGE
        # ==========================

        save_customer_message(
            company_id,
            customer_id,
            conversation_id,
            message,
            channel
        )



        # ==========================
        # INTENT
        # ==========================

        intent_data = detect_intent(
            message,
            company_id
        )


        intent = intent_data.get(
            "intent"
        )


        confidence = intent_data.get(
            "confidence",
            0
        )



        # ==========================
        # KNOWLEDGE
        # ==========================

        knowledge = search_knowledge(
            message,
            company_id,
            intent
        )



        # ==========================
        # SERVICE
        # ==========================

        service = None


        if intent:

            service = resolve_service(
                intent,
                company_id
            )



        # ==========================
        # EXISTING TICKET
        # ==========================

        existing_ticket = find_open_ticket(
            customer_id,
            intent,
            service["id"]
            if service
            else None
        )



        # ==========================
        # REASONING
        # ==========================

        decision = analyze_context(

            context,

            intent,

            knowledge,

            service,

            existing_ticket

        )



        ticket_id = None



        # ==========================
        # TICKET CREATION
        # ==========================


        if decision["create_ticket"]:


            ticket = create_ticket(

                customer_id,

                service["id"]
                if service
                else None,

                description=message,

                title=
                service["name"]
                if service
                else "Support",

                intent=intent,

                company_id=company_id,

                channel=channel

            )


            if ticket:

                ticket_id = ticket.get(
                    "id"
                )


        elif decision["reuse_ticket"]:

            ticket_id = existing_ticket.get(
                "id"
            )



        # ==========================
        # RESPONSE
        # ==========================

        response = generate_response(

            intent,

            service,

            knowledge,

            ticket_id,

            customer_name,

            decision

        )



        # ==========================
        # SAVE BITEY MESSAGE
        # ==========================


        save_bitey_message(

            company_id,

            customer_id,

            conversation_id,

            response,

            intent,

            confidence,

            service["id"]
            if service
            else None,

            ticket_id,

            channel

        )



        # ==========================
        # MEMORY UPDATE
        # ==========================

        update_conversation(

            conversation_id,

            {

                "last_intent": intent,

                "last_response": response,

                "ticket_id": ticket_id

            }

        )



        return {

            "customer_id": customer_id,

            "conversation_id": conversation_id,

            "response": response,

            "intent": intent,

            "confidence": confidence,

            "service": service,

            "ticket_id": ticket_id,

            "decision": decision,

            "context": context

        }



    except Exception as error:


        print(
            "[BITEY V3 ERROR]",
            error
        )


        return {

            "error": str(error)

        }