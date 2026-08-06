"""
Bitey Customer Context Service V2

Construye contexto completo del cliente:
- Perfil
- Tickets
- Mensajes
- Servicios usados
- Última intención
- Idioma
"""


from app.services.cliente_service import get_customer
from app.services.historial_service import get_messages
from app.services.ticket_service import get_customer_tickets



def build_customer_context(
    customer_id: int,
    company_id: int = 1
):

    # Cliente

    customer = get_customer(
        customer_id,
        company_id
    )


    # Tickets

    tickets = get_customer_tickets(
        customer_id,
        company_id
    )



    # Conversación

    messages = get_messages(
        customer_id,
        company_id
    )



    # Servicios utilizados

    services = []


    for ticket in tickets:

        service_id = ticket.get(
            "service_id"
        )


        if (
            service_id
            and service_id not in services
        ):

            services.append(
                service_id
            )



    # Ticket abierto actual

    active_ticket = None


    for ticket in tickets:

        if ticket.get(
            "status"
        ) == "open":

            active_ticket = ticket

            break



    # Último servicio

    last_service = None


    if active_ticket:

        last_service = {

            "id":
                active_ticket.get(
                    "service_id"
                ),


            "intent":
                active_ticket.get(
                    "intent"
                ),


            "ticket_code":
                active_ticket.get(
                    "ticket_code"
                )
        }



    # Última intención detectada

    last_intent = None


    for message in messages:

        intent = message.get(
            "intent"
        )


        if intent:

            last_intent = intent

            break



    return {

        "customer":
            customer,


        "tickets":
            tickets,


        "messages":
            messages,


        "services":
            services,


        "active_ticket":
            active_ticket,


        "last_service":
            last_service,


        "last_intent":
            last_intent,


        "language_context": {


            "customer_language":
                (
                    customer.get(
                        "preferred_language"
                    )
                    if customer
                    else None
                ),


            "current_language":
                (
                    active_ticket.get(
                        "language"
                    )
                    if active_ticket
                    else None
                )

        },


        "summary": {


            "customer_name":
                (
                    customer.get(
                        "full_name"
                    )
                    if customer
                    else None
                ),


            "email":
                (
                    customer.get(
                        "email"
                    )
                    if customer
                    else None
                ),


            "total_tickets":
                len(tickets),


            "open_tickets":
                [
                    t
                    for t in tickets
                    if t.get("status") == "open"
                ],


            "recent_messages":
                messages[:10]

        }

    }