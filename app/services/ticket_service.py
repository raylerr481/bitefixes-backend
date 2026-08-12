from datetime import datetime

from app.database.supabase import supabase


OPEN_STATUS = "open"

ACTIVE_STATUSES = [
    "open",
    "in_progress",
    "pending",
]


def generate_ticket_number(ticket_id=None):
    """Genera el código del ticket."""

    year = datetime.now().year

    if ticket_id is not None:
        return f"BF-{year}-{int(ticket_id):06d}"

    try:
        result = (
            supabase
            .table("tickets")
            .select("id")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )

        next_id = 1

        if result.data:
            next_id = int(result.data[0]["id"]) + 1

        return f"BF-{year}-{next_id:06d}"

    except Exception as exc:
        print(f"[TICKET] ERROR generando número: {exc}")
        return f"BF-{year}-000001"


def create_ticket(
    customer_id,
    service_id=None,
    title=None,
    description=None,
    intent=None,
    language="es",
    company_id=None,
    channel="website",
    ticket_type="technical_support",
):
    """Crea un nuevo ticket."""

    if customer_id is None:
        print("[TICKET] ERROR: customer_id es obligatorio")
        return None

    now = datetime.now().isoformat()

    data = {
        "customer_id": customer_id,
        "service_id": service_id,
        "title": title or "Solicitud de soporte",
        "description": description,
        "intent": intent,
        "language": language,
        "status": OPEN_STATUS,
        "priority": "normal",
        "company_id": company_id,
        "ticket_type": ticket_type,
        "channel": channel,
        "created_at": now,
        "received_at": now,
    }

    data = {
        key: value
        for key, value in data.items()
        if value is not None
    }

    try:
        result = (
            supabase
            .table("tickets")
            .insert(data)
            .execute()
        )
    except Exception as exc:
        print(f"[TICKET] ERROR creando ticket: {exc}")
        return None

    if not result.data:
        print("[TICKET] ERROR: Supabase no devolvió datos")
        return None

    ticket = result.data[0]

    ticket_id = ticket.get("id")

    if ticket_id is None:
        print("[TICKET] WARNING: ticket creado sin ID")
        return ticket

    ticket_code = generate_ticket_number(ticket_id)

    code_data = {
        "ticket_code": ticket_code,
        "codigo_ticket": ticket_code,
        "updated_at": datetime.now().isoformat(),
    }

    try:
        code_result = (
            supabase
            .table("tickets")
            .update(code_data)
            .eq("id", ticket_id)
            .execute()
        )

        if code_result.data:
            ticket = code_result.data[0]

    except Exception as exc:
        print(
            "[TICKET] WARNING: no se pudo actualizar "
            f"el código: {exc}"
        )

    print(
        "[TICKET] Nuevo ticket creado:",
        ticket.get("ticket_code")
        or ticket.get("codigo_ticket")
        or f"ID-{ticket_id}",
    )

    return ticket


def obtener_ticket(ticket_id):
    """Obtiene un ticket por ID."""

    if ticket_id is None:
        return None

    try:
        result = (
            supabase
            .table("tickets")
            .select("*")
            .eq("id", ticket_id)
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]

    except Exception as exc:
        print(f"[TICKET] ERROR obteniendo ticket: {exc}")

    return None


def get_ticket(ticket_id):
    """Alias en inglés."""
    return obtener_ticket(ticket_id)


def get_tickets(company_id=None):
    """Obtiene todos los tickets."""

    try:
        query = (
            supabase
            .table("tickets")
            .select("*")
        )

        if company_id is not None:
            query = query.eq("company_id", company_id)

        result = (
            query
            .order("created_at", desc=True)
            .execute()
        )

        return result.data or []

    except Exception as exc:
        print(f"[TICKET] ERROR listando tickets: {exc}")
        return []


def listar_tickets(company_id=None):
    """Alias en español."""
    return get_tickets(company_id=company_id)


def get_customer_tickets(
    customer_id,
    company_id=None,
):
    """Obtiene los tickets de un cliente."""

    if customer_id is None:
        return []

    try:
        query = (
            supabase
            .table("tickets")
            .select("*")
            .eq("customer_id", customer_id)
        )

        if company_id is not None:
            query = query.eq("company_id", company_id)

        result = (
            query
            .order("created_at", desc=True)
            .execute()
        )

        return result.data or []

    except Exception as exc:
        print(
            "[TICKET] ERROR obteniendo tickets "
            f"del cliente: {exc}"
        )
        return []


def get_open_ticket(
    customer_id,
    service_id=None,
    company_id=None,
    intent=None,
):
    """
    Busca un ticket activo.

    Todos los filtros proporcionados se aplican.
    """

    if customer_id is None:
        return None

    try:
        query = (
            supabase
            .table("tickets")
            .select("*")
            .eq("customer_id", customer_id)
            .in_("status", ACTIVE_STATUSES)
        )

        if service_id is not None:
            query = query.eq("service_id", service_id)

        if company_id is not None:
            query = query.eq("company_id", company_id)

        if intent is not None:
            query = query.eq("intent", intent)

        result = (
            query
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]

    except Exception as exc:
        print(
            "[TICKET] ERROR buscando ticket abierto:",
            exc,
        )

    return None


def find_open_ticket(
    customer_id,
    intent=None,
    company_id=None,
    service_id=None,
):
    """
    Busca un ticket activo compatible.

    La reutilización exige coincidencia de:

        customer_id
        company_id
        intent
        service_id
    """

    if customer_id is None:
        return None

    try:
        query = (
            supabase
            .table("tickets")
            .select("*")
            .eq("customer_id", customer_id)
            .in_("status", ACTIVE_STATUSES)
        )

        if intent is not None:
            query = query.eq("intent", intent)

        if company_id is not None:
            query = query.eq("company_id", company_id)

        if service_id is not None:
            query = query.eq("service_id", service_id)

        result = (
            query
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if result.data:
            ticket = result.data[0]

            print(
                "[TICKET] Ticket compatible encontrado:",
                ticket.get("ticket_code")
                or ticket.get("codigo_ticket")
                or f"ID-{ticket.get('id')}",
            )

            return ticket

    except Exception as exc:
        print(
            "[TICKET] ERROR buscando ticket compatible:",
            exc,
        )

    print("[TICKET] No existe ticket activo compatible")

    return None


def update_ticket_language(
    ticket_id,
    language,
):
    """Actualiza el idioma del ticket."""

    if ticket_id is None:
        return None

    if not language:
        return obtener_ticket(ticket_id)

    try:
        result = (
            supabase
            .table("tickets")
            .update(
                {
                    "language": language,
                    "updated_at": datetime.now().isoformat(),
                }
            )
            .eq("id", ticket_id)
            .execute()
        )

        if result.data:
            return result.data[0]

    except Exception as exc:
        print(
            "[TICKET] ERROR actualizando idioma:",
            exc,
        )

    return None


def update_ticket(ticket_id, data):
    """Actualiza campos permitidos del ticket."""

    if ticket_id is None:
        return None

    if not data:
        return obtener_ticket(ticket_id)

    allowed_fields = {
        "title",
        "description",
        "intent",
        "service_id",
        "language",
        "status",
        "priority",
        "category",
        "technician_id",
        "device_id",
        "notes",
        "company_id",
        "ticket_type",
        "channel",
        "solution",
        "warranty_days",
        "labor_cost",
        "material_cost",
        "total_cost",
        "started_at",
        "completed_at",
        "delivered_at",
    }

    clean_data = {
        key: value
        for key, value in data.items()
        if key in allowed_fields
    }

    if not clean_data:
        return obtener_ticket(ticket_id)

    clean_data["updated_at"] = datetime.now().isoformat()

    try:
        result = (
            supabase
            .table("tickets")
            .update(clean_data)
            .eq("id", ticket_id)
            .execute()
        )

        if result.data:
            return result.data[0]

    except Exception as exc:
        print(
            "[TICKET] ERROR actualizando ticket:",
            exc,
        )

    return None


def close_ticket(ticket_id, solution=None):
    """Cierra un ticket."""

    if ticket_id is None:
        return None

    now = datetime.now().isoformat()

    data = {
        "status": "closed",
        "completed_at": now,
        "updated_at": now,
    }

    if solution is not None:
        data["solution"] = solution

    try:
        result = (
            supabase
            .table("tickets")
            .update(data)
            .eq("id", ticket_id)
            .execute()
        )

        return result.data or []

    except Exception as exc:
        print(
            "[TICKET] ERROR cerrando ticket:",
            exc,
        )

        return None


def update_ticket_status(ticket_id, status):
    """Actualiza el estado de un ticket."""

    if ticket_id is None or not status:
        return None

    now = datetime.now().isoformat()

    data = {
        "status": status,
        "updated_at": now,
    }

    if status == "closed":
        data["completed_at"] = now

    elif status == "in_progress":
        data["started_at"] = now

    try:
        result = (
            supabase
            .table("tickets")
            .update(data)
            .eq("id", ticket_id)
            .execute()
        )

        return result.data or []

    except Exception as exc:
        print(
            "[TICKET] ERROR actualizando estado:",
            exc,
        )

        return None


def process_ticket(
    company_id,
    customer_id,
    service_id=None,
    intent=None,
    description=None,
    title=None,
    language="es",
    channel="website",
    ticket_type="technical_support",
):
    """
    Punto central para crear o reutilizar tickets.

    Un ticket solamente se reutiliza cuando coincide:

        customer_id
        company_id
        intent
        service_id

    Y además tiene un estado activo.
    """

    print(
        "[TICKET] Procesando:",
        f"customer={customer_id}",
        f"company={company_id}",
        f"service={service_id}",
        f"intent={intent}",
        f"channel={channel}",
    )

    if customer_id is None:
        print(
            "[TICKET] ERROR: customer_id es obligatorio"
        )
        return None

    if company_id is None:
        print(
            "[TICKET] WARNING: company_id no proporcionado"
        )

    existing_ticket = find_open_ticket(
        customer_id=customer_id,
        intent=intent,
        company_id=company_id,
        service_id=service_id,
    )

    if existing_ticket:

        ticket_id = existing_ticket.get("id")

        ticket_code = (
            existing_ticket.get("ticket_code")
            or existing_ticket.get("codigo_ticket")
            or f"ID-{ticket_id}"
        )

        print(
            "[TICKET] Ticket activo existente reutilizado:",
            ticket_code,
        )

        current_language = existing_ticket.get("language")

        if (
            language
            and language != current_language
        ):
            updated_ticket = update_ticket_language(
                ticket_id,
                language,
            )

            if updated_ticket:
                existing_ticket = updated_ticket

        current_ticket_code = (
            existing_ticket.get("ticket_code")
        )

        current_codigo_ticket = (
            existing_ticket.get("codigo_ticket")
        )

        if (
            ticket_id is not None
            and (
                not current_ticket_code
                or not current_codigo_ticket
            )
        ):
            generated_code = generate_ticket_number(
                ticket_id
            )

            code_data = {
                "ticket_code": generated_code,
                "codigo_ticket": generated_code,
                "updated_at": datetime.now().isoformat(),
            }

            try:
                code_result = (
                    supabase
                    .table("tickets")
                    .update(code_data)
                    .eq("id", ticket_id)
                    .execute()
                )

                if code_result.data:
                    existing_ticket = code_result.data[0]

            except Exception as exc:
                print(
                    "[TICKET] WARNING: no se pudo sincronizar "
                    f"el código: {exc}"
                )

        return existing_ticket

    print(
        "[TICKET] No existe ticket compatible. "
        "Creando nuevo ticket..."
    )

    ticket = create_ticket(
        customer_id=customer_id,
        service_id=service_id,
        title=title,
        description=description,
        intent=intent,
        language=language,
        company_id=company_id,
        channel=channel,
        ticket_type=ticket_type,
    )

    if not ticket:
        print(
            "[TICKET] ERROR: no se pudo crear el ticket"
        )
        return None

    print(
        "[TICKET] Ticket creado:",
        ticket.get("ticket_code")
        or ticket.get("codigo_ticket"),
    )

    return ticket


def procesar_ticket(
    company_id,
    customer_id,
    service_id=None,
    intent=None,
    description=None,
    title=None,
    language="es",
    channel="website",
    ticket_type="technical_support",
):
    """Alias en español."""

    return process_ticket(
        company_id=company_id,
        customer_id=customer_id,
        service_id=service_id,
        intent=intent,
        description=description,
        title=title,
        language=language,
        channel=channel,
        ticket_type=ticket_type,
    )


def find_ticket(
    customer_id,
    intent=None,
    company_id=None,
    service_id=None,
):
    """Alias compatible."""

    return find_open_ticket(
        customer_id=customer_id,
        intent=intent,
        company_id=company_id,
        service_id=service_id,
    )
