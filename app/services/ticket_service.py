"""
BiteFixes / Bitey AI
Ticket Service V9

Responsabilidades:
- Crear tickets
- Consultar tickets del cliente
- Detectar tickets abiertos
- Evitar duplicados
- Reutilizar tickets existentes
- Sincronizar idioma
- Actualizar contexto del ticket
- Preparado para CRM
"""


from datetime import datetime
from app.database.supabase import supabase



# ============================================================
# Obtener tickets del cliente
# ============================================================

def get_customer_tickets(
    customer_id: int,
    company_id: int = 1
):

    try:

        response = (
            supabase
            .table("tickets")
            .select("*")
            .eq("customer_id", customer_id)
            .eq("company_id", company_id)
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        return response.data or []


    except Exception as e:

        print(
            "[GET CUSTOMER TICKETS ERROR]",
            e
        )

        return []



# ============================================================
# Obtener tickets abiertos
# ============================================================

def get_open_customer_tickets(
    customer_id: int,
    company_id: int = 1
):

    tickets = get_customer_tickets(
        customer_id,
        company_id
    )


    open_status = [
        "open",
        "pending",
        "in_progress"
    ]


    return [

        ticket

        for ticket in tickets

        if ticket.get("status")
        in open_status

    ]



# ============================================================
# Buscar ticket abierto por intención
# ============================================================

def find_open_ticket_by_intent(
    customer_id: int,
    intent: str,
    company_id: int = 1
):

    tickets = get_open_customer_tickets(
        customer_id,
        company_id
    )


    for ticket in tickets:

        if ticket.get("intent") == intent:

            return ticket


    return None



# ============================================================
# Generar código ticket
# ============================================================

def generate_ticket_code(
    ticket_id: int
):

    year = datetime.now().year


    return (
        f"BF-{year}-{ticket_id:06d}"
    )



# ============================================================
# Crear ticket
# ============================================================

def create_ticket(
    customer_id: int,
    company_id: int,
    title: str,
    description: str,
    intent: str,
    service_id: int = None,
    language: str = "pt-BR",
    ticket_type: str = "technical_support",
    channel: str = "website"
):

    try:


        # ----------------------------------------
        # Buscar ticket existente
        # ----------------------------------------

        existing = find_open_ticket_by_intent(
            customer_id,
            intent,
            company_id
        )


        if existing:


            print(
                "[TICKET REUSED]",
                existing.get(
                    "ticket_code"
                )
            )


            # Actualizar idioma
            if (
                language
                and
                existing.get("language")
                != language
            ):

                update_ticket_language(
                    existing["id"],
                    language
                )


            return existing



        # ----------------------------------------
        # Crear nuevo ticket
        # ----------------------------------------

        now = datetime.utcnow().isoformat()


        data = {

            "customer_id":
                customer_id,


            "company_id":
                company_id,


            "title":
                title,


            "description":
                description,


            "intent":
                intent,


            "service_id":
                service_id,


            "status":
                "open",


            "priority":
                "normal",


            "language":
                language,


            "ticket_type":
                ticket_type,


            "channel":
                channel,


            "received_at":
                now,


            "created_at":
                now

        }



        result = (

            supabase
            .table("tickets")
            .insert(data)
            .execute()

        )



        if not result.data:

            return None



        ticket = result.data[0]



        # ----------------------------------------
        # Crear código BF
        # ----------------------------------------

        code = generate_ticket_code(
            ticket["id"]
        )



        updated = (

            supabase
            .table("tickets")
            .update(
                {
                    "ticket_code":
                    code
                }
            )
            .eq(
                "id",
                ticket["id"]
            )
            .execute()

        )



        return updated.data[0]



    except Exception as e:


        print(
            "[CREATE TICKET ERROR]",
            e
        )


        return None




# ============================================================
# Actualizar idioma ticket
# ============================================================

def update_ticket_language(
    ticket_id: int,
    language: str
):

    try:


        response = (

            supabase
            .table("tickets")
            .update(
                {
                    "language":
                    language
                }
            )
            .eq(
                "id",
                ticket_id
            )
            .execute()

        )


        return response.data



    except Exception as e:


        print(
            "[UPDATE LANGUAGE ERROR]",
            e
        )


        return None



# ============================================================
# Actualizar ticket
# ============================================================

def update_ticket(
    ticket_id: int,
    data: dict
):

    try:


        response = (

            supabase
            .table("tickets")
            .update(data)
            .eq(
                "id",
                ticket_id
            )
            .execute()

        )


        return response.data



    except Exception as e:


        print(
            "[UPDATE TICKET ERROR]",
            e
        )


        return None



# ============================================================
# Cerrar ticket
# ============================================================

def close_ticket(
    ticket_id: int,
    solution: str = None
):

    try:


        data = {


            "status":
                "completed",


            "completed_at":
                datetime.utcnow().isoformat()

        }



        if solution:


            data["solution"] = solution



        response = (

            supabase
            .table("tickets")
            .update(data)
            .eq(
                "id",
                ticket_id
            )
            .execute()

        )


        return response.data



    except Exception as e:


        print(
            "[CLOSE TICKET ERROR]",
            e
        )


        return None



# ============================================================
# Obtener ticket por ID
# ============================================================

def get_ticket(
    ticket_id: int
):

    try:


        response = (

            supabase
            .table("tickets")
            .select("*")
            .eq(
                "id",
                ticket_id
            )
            .single()
            .execute()

        )


        return response.data



    except Exception as e:


        print(
            "[GET TICKET ERROR]",
            e
        )


        return None
        """
BiteFixes / Bitey AI
Ticket Service V9

Responsabilidades:
- Crear tickets
- Consultar tickets del cliente
- Detectar tickets abiertos
- Evitar duplicados
- Reutilizar tickets existentes
- Sincronizar idioma
- Actualizar contexto del ticket
- Preparado para CRM
"""


from datetime import datetime
from app.database.supabase import supabase



# ============================================================
# Obtener tickets del cliente
# ============================================================

def get_customer_tickets(
    customer_id: int,
    company_id: int = 1
):

    try:

        response = (
            supabase
            .table("tickets")
            .select("*")
            .eq("customer_id", customer_id)
            .eq("company_id", company_id)
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        return response.data or []


    except Exception as e:

        print(
            "[GET CUSTOMER TICKETS ERROR]",
            e
        )

        return []



# ============================================================
# Obtener tickets abiertos
# ============================================================

def get_open_customer_tickets(
    customer_id: int,
    company_id: int = 1
):

    tickets = get_customer_tickets(
        customer_id,
        company_id
    )


    open_status = [
        "open",
        "pending",
        "in_progress"
    ]


    return [

        ticket

        for ticket in tickets

        if ticket.get("status")
        in open_status

    ]



# ============================================================
# Buscar ticket abierto por intención
# ============================================================

def find_open_ticket_by_intent(
    customer_id: int,
    intent: str,
    company_id: int = 1
):

    tickets = get_open_customer_tickets(
        customer_id,
        company_id
    )


    for ticket in tickets:

        if ticket.get("intent") == intent:

            return ticket


    return None



# ============================================================
# Generar código ticket
# ============================================================

def generate_ticket_code(
    ticket_id: int
):

    year = datetime.now().year


    return (
        f"BF-{year}-{ticket_id:06d}"
    )



# ============================================================
# Crear ticket
# ============================================================

def create_ticket(
    customer_id: int,
    company_id: int,
    title: str,
    description: str,
    intent: str,
    service_id: int = None,
    language: str = "pt-BR",
    ticket_type: str = "technical_support",
    channel: str = "website"
):

    try:


        # ----------------------------------------
        # Buscar ticket existente
        # ----------------------------------------

        existing = find_open_ticket_by_intent(
            customer_id,
            intent,
            company_id
        )


        if existing:


            print(
                "[TICKET REUSED]",
                existing.get(
                    "ticket_code"
                )
            )


            # Actualizar idioma
            if (
                language
                and
                existing.get("language")
                != language
            ):

                update_ticket_language(
                    existing["id"],
                    language
                )


            return existing



        # ----------------------------------------
        # Crear nuevo ticket
        # ----------------------------------------

        now = datetime.utcnow().isoformat()


        data = {

            "customer_id":
                customer_id,


            "company_id":
                company_id,


            "title":
                title,


            "description":
                description,


            "intent":
                intent,


            "service_id":
                service_id,


            "status":
                "open",


            "priority":
                "normal",


            "language":
                language,


            "ticket_type":
                ticket_type,


            "channel":
                channel,


            "received_at":
                now,


            "created_at":
                now

        }



        result = (

            supabase
            .table("tickets")
            .insert(data)
            .execute()

        )



        if not result.data:

            return None



        ticket = result.data[0]



        # ----------------------------------------
        # Crear código BF
        # ----------------------------------------

        code = generate_ticket_code(
            ticket["id"]
        )



        updated = (

            supabase
            .table("tickets")
            .update(
                {
                    "ticket_code":
                    code
                }
            )
            .eq(
                "id",
                ticket["id"]
            )
            .execute()

        )



        return updated.data[0]



    except Exception as e:


        print(
            "[CREATE TICKET ERROR]",
            e
        )


        return None




# ============================================================
# Actualizar idioma ticket
# ============================================================

def update_ticket_language(
    ticket_id: int,
    language: str
):

    try:


        response = (

            supabase
            .table("tickets")
            .update(
                {
                    "language":
                    language
                }
            )
            .eq(
                "id",
                ticket_id
            )
            .execute()

        )


        return response.data



    except Exception as e:


        print(
            "[UPDATE LANGUAGE ERROR]",
            e
        )


        return None



# ============================================================
# Actualizar ticket
# ============================================================

def update_ticket(
    ticket_id: int,
    data: dict
):

    try:


        response = (

            supabase
            .table("tickets")
            .update(data)
            .eq(
                "id",
                ticket_id
            )
            .execute()

        )


        return response.data



    except Exception as e:


        print(
            "[UPDATE TICKET ERROR]",
            e
        )


        return None



# ============================================================
# Cerrar ticket
# ============================================================

def close_ticket(
    ticket_id: int,
    solution: str = None
):

    try:


        data = {


            "status":
                "completed",


            "completed_at":
                datetime.utcnow().isoformat()

        }



        if solution:


            data["solution"] = solution



        response = (

            supabase
            .table("tickets")
            .update(data)
            .eq(
                "id",
                ticket_id
            )
            .execute()

        )


        return response.data



    except Exception as e:


        print(
            "[CLOSE TICKET ERROR]",
            e
        )


        return None



# ============================================================
# Obtener ticket por ID
# ============================================================

def get_ticket(
    ticket_id: int
):

    try:


        response = (

            supabase
            .table("tickets")
            .select("*")
            .eq(
                "id",
                ticket_id
            )
            .single()
            .execute()

        )


        return response.data



    except Exception as e:


        print(
            "[GET TICKET ERROR]",
            e
        )


        return None