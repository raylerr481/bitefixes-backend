"""
BiteFixes Quote Service V1.1

Responsibilities:
- Create Quotes
- Find Quotes
- Update Quotes
- Delete Quotes
- List Quotes
- Approve Quotes
- Reject Quotes
- Expire Quotes
- Convert Quotes to Work Orders
- Generate Quote Numbers
- Prevent Duplicate Quotes
- API Compatibility Wrappers
"""

from datetime import datetime, timedelta
from typing import Optional

from app.database.supabase import database


# =====================================================
# GENERATE QUOTE NUMBER
# =====================================================

def generate_quote_number(
    quote_id: int
):
    """
    Generates:

    Q-2026-000001
    """

    year = datetime.now().year

    return f"Q-{year}-{quote_id:06d}"


# =====================================================
# FIND OPEN QUOTE
# =====================================================

def find_open_quote(
    customer_id: int,
    service_id: Optional[int] = None
):
    """
    Returns latest active quote.
    Prevents duplicate active quotes.
    """

    try:

        query = (
            database
            .table("quotes")
            .select("*")
            .eq(
                "customer_id",
                customer_id
            )
            .in_(
                "status",
                [
                    "draft",
                    "pending",
                    "sent"
                ]
            )
        )


        if service_id is not None:

            query = query.eq(
                "service_id",
                service_id
            )


        response = (
            query
            .order(
                "created_at",
                desc=True
            )
            .limit(1)
            .execute()
        )


        if response.data:

            return response.data[0]


        return None


    except Exception as error:

        print(
            "[FIND OPEN QUOTE ERROR]",
            error
        )

        return None



# =====================================================
# GET QUOTE
# =====================================================

def get_quote(
    quote_id: int
):

    try:

        response = (
            database
            .table("quotes")
            .select("*")
            .eq(
                "id",
                quote_id
            )
            .execute()
        )


        if response.data:

            return response.data[0]


        return None


    except Exception as error:

        print(
            "[GET QUOTE ERROR]",
            error
        )

        return None



# =====================================================
# LIST QUOTES
# =====================================================

def list_quotes(
    company_id: int = 1,
    customer_id: Optional[int] = None
):

    try:

        query = (
            database
            .table("quotes")
            .select("*")
            .eq(
                "company_id",
                company_id
            )
        )


        if customer_id is not None:

            query = query.eq(
                "customer_id",
                customer_id
            )


        response = (
            query
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )


        return response.data or []


    except Exception as error:

        print(
            "[LIST QUOTES ERROR]",
            error
        )

        return []
        """
BiteFixes Quote Service V1.1

Responsibilities:
- Create Quotes
- Find Quotes
- Update Quotes
- Delete Quotes
- List Quotes
- Approve Quotes
- Reject Quotes
- Expire Quotes
- Convert Quotes to Work Orders
- Generate Quote Numbers
- Prevent Duplicate Quotes
- API Compatibility Wrappers
"""

from datetime import datetime, timedelta
from typing import Optional

from app.database.supabase import database


# =====================================================
# GENERATE QUOTE NUMBER
# =====================================================

def generate_quote_number(
    quote_id: int
):
    """
    Generates:

    Q-2026-000001
    """

    year = datetime.now().year

    return f"Q-{year}-{quote_id:06d}"


# =====================================================
# FIND OPEN QUOTE
# =====================================================

def find_open_quote(
    customer_id: int,
    service_id: Optional[int] = None
):
    """
    Returns latest active quote.
    Prevents duplicate active quotes.
    """

    try:

        query = (
            database
            .table("quotes")
            .select("*")
            .eq(
                "customer_id",
                customer_id
            )
            .in_(
                "status",
                [
                    "draft",
                    "pending",
                    "sent"
                ]
            )
        )


        if service_id is not None:

            query = query.eq(
                "service_id",
                service_id
            )


        response = (
            query
            .order(
                "created_at",
                desc=True
            )
            .limit(1)
            .execute()
        )


        if response.data:

            return response.data[0]


        return None


    except Exception as error:

        print(
            "[FIND OPEN QUOTE ERROR]",
            error
        )

        return None



# =====================================================
# GET QUOTE
# =====================================================

def get_quote(
    quote_id: int
):

    try:

        response = (
            database
            .table("quotes")
            .select("*")
            .eq(
                "id",
                quote_id
            )
            .execute()
        )


        if response.data:

            return response.data[0]


        return None


    except Exception as error:

        print(
            "[GET QUOTE ERROR]",
            error
        )

        return None



# =====================================================
# LIST QUOTES
# =====================================================

def list_quotes(
    company_id: int = 1,
    customer_id: Optional[int] = None
):

    try:

        query = (
            database
            .table("quotes")
            .select("*")
            .eq(
                "company_id",
                company_id
            )
        )


        if customer_id is not None:

            query = query.eq(
                "customer_id",
                customer_id
            )


        response = (
            query
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )


        return response.data or []


    except Exception as error:

        print(
            "[LIST QUOTES ERROR]",
            error
        )

        return []
        # =====================================================
# CREATE QUOTE
# =====================================================

def create_quote(
    company_id: int,
    customer_id: int,
    service_id: Optional[int],
    title: str,
    description: str,
    subtotal: float = 0,
    discount: float = 0,
    tax: float = 0,
    currency: str = "BRL",
    valid_days: int = 15,
    ticket_id: Optional[int] = None,
    lead_id: Optional[int] = None
):

    """
    Creates a new quote.

    Prevents duplicate active quotes.
    """

    try:

        # ---------------------------------------------
        # Avoid duplicate active quote
        # ---------------------------------------------

        existing = find_open_quote(
            customer_id=customer_id,
            service_id=service_id
        )


        if existing:

            print(
                "[EXISTING QUOTE]",
                existing.get("quote_number")
            )

            return existing



        # ---------------------------------------------
        # Calculate totals
        # ---------------------------------------------

        total = (
            subtotal
            - discount
            + tax
        )


        valid_until = (
            datetime.now()
            + timedelta(days=valid_days)
        ).isoformat()



        data = {

            "company_id": company_id,

            "customer_id": customer_id,

            "service_id": service_id,

            "ticket_id": ticket_id,

            "lead_id": lead_id,

            "title": title,

            "description": description,

            "status": "draft",

            "subtotal": subtotal,

            "discount": discount,

            "tax": tax,

            "total": total,

            "currency": currency,

            "valid_until": valid_until

        }



        response = (
            database
            .table("quotes")
            .insert(data)
            .execute()
        )


        if not response.data:

            return None



        quote = response.data[0]



        # ---------------------------------------------
        # Generate quote number
        # ---------------------------------------------

        quote_number = generate_quote_number(
            quote["id"]
        )


        update = (
            database
            .table("quotes")
            .update(
                {
                    "quote_number": quote_number
                }
            )
            .eq(
                "id",
                quote["id"]
            )
            .execute()
        )


        if update.data:

            quote = update.data[0]



        print(
            "[NEW QUOTE]",
            quote_number
        )


        return quote



    except Exception as error:

        print(
            "[CREATE QUOTE ERROR]",
            error
        )

        return None



# =====================================================
# UPDATE QUOTE
# =====================================================

def update_quote(
    quote_id: int,
    **fields
):

    try:

        if not fields:

            return None



        response = (
            database
            .table("quotes")
            .update(fields)
            .eq(
                "id",
                quote_id
            )
            .execute()
        )


        if response.data:

            print(
                "[QUOTE UPDATED]",
                quote_id
            )


            return response.data[0]



        return None



    except Exception as error:

        print(
            "[UPDATE QUOTE ERROR]",
            error
        )


        return None



# =====================================================
# PROCESS QUOTE
# =====================================================

def process_quote(
    company_id: int,
    customer_id: int,
    service_id: Optional[int],
    description: str,
    title: str,
    subtotal: float = 0,
    discount: float = 0,
    tax: float = 0,
    currency: str = "BRL",
    ticket_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    create_new_quote: bool = False
):

    """
    Compatibility processor.
    """

    if not create_new_quote:

        return None



    return create_quote(

        company_id=company_id,

        customer_id=customer_id,

        service_id=service_id,

        title=title,

        description=description,

        subtotal=subtotal,

        discount=discount,

        tax=tax,

        currency=currency,

        ticket_id=ticket_id,

        lead_id=lead_id

    )
# =====================================================
# APPROVE QUOTE
# =====================================================

def approve_quote(
    quote_id: int
):

    try:

        response = (
            database
            .table("quotes")
            .update(
                {
                    "status": "accepted",
                    "updated_at": datetime.now().isoformat()
                }
            )
            .eq(
                "id",
                quote_id
            )
            .execute()
        )


        if response.data:

            print(
                "[QUOTE APPROVED]",
                quote_id
            )

            return response.data[0]


        return None


    except Exception as error:

        print(
            "[APPROVE QUOTE ERROR]",
            error
        )

        return None



# =====================================================
# REJECT QUOTE
# =====================================================

def reject_quote(
    quote_id: int
):

    try:

        response = (
            database
            .table("quotes")
            .update(
                {
                    "status": "rejected",
                    "updated_at": datetime.now().isoformat()
                }
            )
            .eq(
                "id",
                quote_id
            )
            .execute()
        )


        if response.data:

            print(
                "[QUOTE REJECTED]",
                quote_id
            )

            return response.data[0]


        return None


    except Exception as error:

        print(
            "[REJECT QUOTE ERROR]",
            error
        )

        return None



# =====================================================
# EXPIRE QUOTE
# =====================================================

def expire_quote(
    quote_id: int
):

    try:

        response = (
            database
            .table("quotes")
            .update(
                {
                    "status": "expired",
                    "updated_at": datetime.now().isoformat()
                }
            )
            .eq(
                "id",
                quote_id
            )
            .execute()
        )


        if response.data:

            print(
                "[QUOTE EXPIRED]",
                quote_id
            )

            return response.data[0]


        return None


    except Exception as error:

        print(
            "[EXPIRE QUOTE ERROR]",
            error
        )

        return None



# =====================================================
# DELETE QUOTE
# =====================================================

def delete_quote(
    quote_id: int
):

    try:

        response = (
            database
            .table("quotes")
            .delete()
            .eq(
                "id",
                quote_id
            )
            .execute()
        )


        print(
            "[QUOTE DELETED]",
            quote_id
        )


        return response.data



    except Exception as error:

        print(
            "[DELETE QUOTE ERROR]",
            error
        )

        return None



# =====================================================
# CONVERT TO WORK ORDER
# =====================================================

def convert_to_work_order(
    quote_id: int
):

    """
    Converts quote status.

    Future:
    - Create Work Order
    - Assign technician
    - Create service workflow
    """

    try:

        quote = get_quote(
            quote_id
        )


        if not quote:

            return None



        response = (
            database
            .table("quotes")
            .update(
                {
                    "status": "converted",
                    "updated_at": datetime.now().isoformat()
                }
            )
            .eq(
                "id",
                quote_id
            )
            .execute()
        )


        if response.data:

            print(
                "[QUOTE CONVERTED]",
                quote_id
            )


            return {

                "success": True,

                "quote": response.data[0],

                "work_order": None,

                "message":
                "Ready for Work Order Service."

            }


        return None



    except Exception as error:

        print(
            "[CONVERT QUOTE ERROR]",
            error
        )

        return None



# =====================================================
# COMPATIBILITY WRAPPERS
# =====================================================

def crear_presupuesto(
    company_id=1,
    customer_id=None,
    service_id=None,
    title="Quote",
    description="",
    subtotal=0,
    discount=0,
    tax=0,
    currency="BRL",
    ticket_id=None,
    lead_id=None
):

    return create_quote(

        company_id=company_id,

        customer_id=customer_id,

        service_id=service_id,

        title=title,

        description=description,

        subtotal=subtotal,

        discount=discount,

        tax=tax,

        currency=currency,

        ticket_id=ticket_id,

        lead_id=lead_id

    )



def obtener_presupuesto(
    quote_id
):

    return get_quote(
        quote_id
    )



def listar_presupuestos(
    company_id=1,
    customer_id=None
):

    return list_quotes(

        company_id=company_id,

        customer_id=customer_id

    )



# =====================================================
# LEGACY ALIASES
# =====================================================

find_quote = find_open_quote

buscar_presupuesto = get_quote

actualizar_presupuesto = update_quote

aprobar_presupuesto = approve_quote

rechazar_presupuesto = reject_quote

expirar_presupuesto = expire_quote

eliminar_presupuesto = delete_quote

procesar_presupuesto = process_quote



# =====================================================
# MODULE EXPORTS
# =====================================================

__all__ = [

    "generate_quote_number",

    "find_open_quote",

    "find_quote",

    "get_quote",

    "list_quotes",

    "create_quote",

    "update_quote",

    "process_quote",

    "approve_quote",

    "reject_quote",

    "expire_quote",

    "delete_quote",

    "convert_to_work_order",

    "crear_presupuesto",

    "obtener_presupuesto",

    "listar_presupuestos"

]