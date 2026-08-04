"""
BiteFixes Bitey AI Core Engine

Central AI orchestration layer.

Flow:

Customer
    |
Conversation
    |
Memory
    |
Message
    |
Intent Detection
    |
Knowledge Base
    |
Service Resolver
    |
Ticket Manager
    |
Response
    |
Memory Update

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

from app.services.chat_memory import (
    build_memory_context,
    get_last_intent
)

from app.services.ia_engine import (
    prepare_conversation_context
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

            company_id=company_id,

            phone=whatsapp,

            full_name=customer_name

        )


        if not customer:

            return {
                "error":"customer_failed"
            }


        customer_id = customer["id"]



        # ==========================
        # MEMORY BEFORE PROCESS
        # ==========================

        memory = build_memory_context(
            customer_id,
            5
        )


        previous_intent = get_last_intent(
            customer_id
        )



        ai_context = prepare_conversation_context(

            message,

            memory,

            previous_intent

        )



        # ==========================
        # CONVERSATION
        # ==========================


        conversation = get_or_create_conversation(

            customer_id,

            channel

        )


        if not conversation:

            return {
                "error":"conversation_failed"
            }



        conversation_id = conversation["id"]




        # ==========================
        # SAVE CUSTOMER MESSAGE
        # ==========================


        save_customer_message(

            company_id=company_id,

            customer_id=customer_id,

            conversation_id=conversation_id,

            message=message,

            channel=channel

        )



        # ==========================
        # INTENT
        # ==========================


        intent_result = detect_intent(

            message,

            company_id

        )


        intent = intent_result.get(
            "intent"
        )


        confidence = intent_result.get(
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


        response = None


        requires_ticket = True



        if knowledge:


            response = knowledge.get(
                "answer"
            )


            requires_ticket = knowledge.get(
                "requires_ticket",
                True
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
        # TICKET CONTROL
        # ==========================


        ticket_id = None



        if requires_ticket and service:



            existing = find_open_ticket(

                customer_id,

                intent,

                service["id"]

            )



            if existing:


                ticket_id = existing.get(
                    "id"
                )



            else:


                ticket_type="support"


                if intent=="ai_assistant":

                    ticket_type="sales"



                ticket=create_ticket(

                    customer_id=customer_id,

                    service_id=service["id"],

                    description=message,

                    title=service["name"],

                    intent=intent,

                    company_id=company_id,

                    channel=channel,

                    ticket_type=ticket_type

                )



                if ticket:

                    ticket_id=ticket.get(
                        "id"
                    )




        # ==========================
        # RESPONSE FALLBACK
        # ==========================


        if not response:


            if service:


                response=(

                    "Podemos ayudarte con "

                    + service["name"]

                )


            else:


                response=(

                    "Gracias por contactar BiteFixes."

                )




        if service:


            response += (

                "\n\nServicio: "

                + service["name"]

            )



        if ticket_id:


            response += (

                "\nTicket asociado: #"

                + str(ticket_id)

            )




        # ==========================
        # SAVE BITEY
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
        # UPDATE MEMORY
        # ==========================


        update_conversation(

            conversation_id,

            {

                "last_intent":intent,

                "last_response":response,

                "ticket_id":ticket_id

            }

        )




        return {


            "customer_id":customer_id,


            "conversation_id":conversation_id,


            "response":response,


            "intent":intent,


            "confidence":confidence,


            "service":service,


            "ticket_id":ticket_id,


            "channel":channel,


            "memory_size":len(memory),


            "previous_intent":previous_intent

        }



    except Exception as error:


        print(
            "[BITEY CORE ERROR]",
            error
        )


        return {

            "error":str(error)

        }