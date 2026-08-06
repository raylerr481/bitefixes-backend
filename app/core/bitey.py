"""
=====================================================
Bitey Core V16.2
=====================================================

Main AI Orchestrator

Flow:

Customer
 |
Language Detection
 |
Customer Context
 |
Conversation
 |
Save Customer Message
 |
Intent Detection
 |
Knowledge Search
 |
Decision Engine
 |
 +--> Ticket Service
 |
 +--> Quote Service
 |
Notification
 |
Response Builder
 |
Save AI Message
 |
Update Conversation
 |
Return Result

=====================================================
"""


from app.services.customer_service import (
    get_or_create_customer
)

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

from app.services.quote_service import (
    create_quote
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



# =====================================================
# PROCESS MESSAGE
# =====================================================


def process_message(
    company_id: int,
    message: str,
    whatsapp: str,
    customer_name: str,
    channel: str = "website"
):


    print("\n==============================")
    print("BITEY CORE V16.2")
    print("==============================")



    try:



        # =================================================
        # LANGUAGE
        # =================================================


        language = detect_language(
            message
        )


        print(
            "[LANGUAGE]",
            language
        )



        # =================================================
        # CUSTOMER
        # =================================================


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



        # =================================================
        # CONVERSATION
        # =================================================


        conversation = get_or_create_conversation(

            customer_id,

            channel

        )


        conversation_id = conversation["id"]



        print(
            "[CONVERSATION]",
            conversation_id
        )



        # =================================================
        # MEMORY
        # =================================================


        context = build_customer_context(

            customer_id,

            company_id

        )


        memory = context.get(

            "summary",

            {}

        )



        # =================================================
        # SAVE CUSTOMER MESSAGE
        # =================================================


        save_customer_message(

            company_id=company_id,

            customer_id=customer_id,

            conversation_id=conversation_id,

            message=message,

            channel=channel

        )



        print(
            "[CUSTOMER MESSAGE SAVED]"
        )



        # =================================================
        # INTENT
        # =================================================


        intent = detect_intent(

            message,

            company_id

        )


        intent_name = intent.get(
            "intent"
        )


        confidence = intent.get(

            "confidence",

            0

        )



        print(
            "[INTENT]",
            intent
        )



        # =================================================
        # KNOWLEDGE
        # =================================================


        knowledge = search_knowledge(

            message,

            company_id,

            intent_name,

            language

        )



        print(
            "[KNOWLEDGE]",
            bool(knowledge)
        )



        # =================================================
        # DECISION ENGINE
        # =================================================


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


                "action":
                    "support",


                "create_ticket":
                    True,


                "ticket_type":
                    "technical_support",


                "response":
                    {

                    "response":
                        "Solicitud recibida."

                    }

            }



        print(
            "[DECISION]",
            decision
        )



        service_id = decision.get(
            "service_id"
        )



        # =================================================
        # TICKET
        # =================================================


        ticket = process_ticket(

            company_id=company_id,

            customer_id=customer_id,

            service_id=service_id,

            intent=intent_name,

            description=message,

            title=(

                decision

                .get(
                    "service",
                    {}
                )

                .get(
                    "name",
                    intent_name or "Support"
                )

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

            ),

            requires_quote=decision.get(

                "requires_quote",

                False

            )

        )



        print(
            "[TICKET]",
            ticket
        )



        ticket_id = (

            ticket.get("id")

            if ticket

            else None

        )



        # =================================================
        # QUOTE
        # =================================================


        quote = None



        if (

            decision.get(
                "requires_quote",
                False
            )

            and ticket

        ):



            quote = create_quote(

                company_id=company_id,

                customer_id=customer_id,

                service_id=service_id,

                title=ticket.get(
                    "title",
                    "Quote"
                ),

                description=message,

                ticket_id=ticket_id

            )



        # =================================================
        # RESPONSE BUILDER
        # =================================================


        response = build_response(

            decision=decision,

            ticket=ticket,

            knowledge=knowledge,

            language=language

        )



        print(
            "[RESPONSE]",
            response
        )



        # =================================================
        # NOTIFICATION
        # =================================================


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
                        quote.get("id")
                        if quote
                        else None

                }

            )



        # =================================================
        # SAVE AI MESSAGE
        # =================================================


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



        print(
            "[BITEY MESSAGE SAVED]"
        )



        # =================================================
        # UPDATE CONTEXT
        # =================================================


        update_conversation_context(

            conversation_id,

            intent=intent_name,

            response=response,

            ticket_id=ticket_id

        )



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
                response

        }



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
                "Error procesando solicitud."

        }