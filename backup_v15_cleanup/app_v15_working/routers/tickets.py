# app/routers/tickets.py

from fastapi import APIRouter, HTTPException

from app.services.ticket_service import (
    listar_tickets,
    obtener_ticket,
    crear_ticket,
    actualizar_ticket,
    cerrar_ticket,
    cancelar_ticket,
)

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

# =====================================================
# LISTAR TICKETS
# =====================================================

@router.get("/")
def listar():
    return listar_tickets()


# =====================================================
# OBTENER TICKET
# =====================================================

@router.get("/{ticket_id}")
def obtener(ticket_id: int):

    ticket = obtener_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket no encontrado"
        )

    return ticket


# =====================================================
# CREAR TICKET
# =====================================================

@router.post("/")
def crear(
    cliente_id: int,
    servicio_id: int,
    descripcion: str,
    titulo: str = "Nuevo Ticket"
):

    ticket = crear_ticket(
        cliente_id=cliente_id,
        servicio_id=servicio_id,
        descripcion=descripcion,
        titulo=titulo
    )

    if ticket is None:
        raise HTTPException(
            status_code=500,
            detail="No fue posible crear el ticket."
        )

    return ticket


# =====================================================
# ACTUALIZAR TICKET
# =====================================================

@router.put("/{ticket_id}")
def actualizar(
    ticket_id: int,
    datos: dict
):

    ticket = actualizar_ticket(
        ticket_id,
        datos
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket no encontrado."
        )

    return ticket


# =====================================================
# CERRAR TICKET
# =====================================================

@router.put("/{ticket_id}/cerrar")
def cerrar(ticket_id: int):

    ticket = cerrar_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket no encontrado."
        )

    return ticket


# =====================================================
# CANCELAR TICKET
# =====================================================

@router.put("/{ticket_id}/cancelar")
def cancelar(ticket_id: int):

    ticket = cancelar_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket no encontrado."
        )

    return ticket