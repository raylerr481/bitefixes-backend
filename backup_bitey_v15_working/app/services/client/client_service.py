"""
Client Service

Customer identity management layer.

Responsibilities:

- Find customers by WhatsApp
- Create customers
- Update customers
- Maintain SaaS company isolation

Database:
clientes
"""


from datetime import datetime, timezone


from app.database.supabase import supabase



DEFAULT_COMPANY_ID = 1



# =====================================================
# GET CLIENT BY WHATSAPP
# =====================================================

def get_client_by_whatsapp(
    whatsapp: str,
    company_id: int = DEFAULT_COMPANY_ID
):

    try:

        result = (
            supabase
            .table("clientes")
            .select("*")
            .eq(
                "empresa_id",
                company_id
            )
            .eq(
                "whatsapp",
                whatsapp
            )
            .limit(1)
            .execute()
        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            f"[CLIENT] get_client_by_whatsapp error: {error}"
        )

        return None



# =====================================================
# CREATE CLIENT
# =====================================================

def create_client(
    whatsapp: str,
    company_id: int = DEFAULT_COMPANY_ID,
    name: str | None = None
):


    now = datetime.now(
        timezone.utc
    ).isoformat()



    client_data = {

        "empresa_id": company_id,

        "nombre": name,

        "whatsapp": whatsapp,

        "activo": True,

        "created_at": now,

        "updated_at": now

    }



    try:

        result = (
            supabase
            .table("clientes")
            .insert(
                client_data
            )
            .execute()
        )


        return result.data[0]


    except Exception as error:

        print(
            f"[CLIENT] create_client error: {error}"
        )

        return None



# =====================================================
# GET OR CREATE CLIENT
# =====================================================

def get_or_create_client(
    whatsapp: str,
    company_id: int = DEFAULT_COMPANY_ID,
    name: str | None = None
):


    client = get_client_by_whatsapp(
        whatsapp=whatsapp,
        company_id=company_id
    )


    if client:

        return client



    return create_client(
        whatsapp=whatsapp,
        company_id=company_id,
        name=name
    )



# =====================================================
# GET CLIENT BY ID
# =====================================================

def get_client(
    client_id: int
):


    try:

        result = (
            supabase
            .table("clientes")
            .select("*")
            .eq(
                "id",
                client_id
            )
            .limit(1)
            .execute()
        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            f"[CLIENT] get_client error: {error}"
        )

        return None



# =====================================================
# UPDATE CLIENT
# =====================================================

def update_client(
    client_id: int,
    data: dict
):


    data["updated_at"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )


    try:

        result = (
            supabase
            .table("clientes")
            .update(data)
            .eq(
                "id",
                client_id
            )
            .execute()
        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            f"[CLIENT] update_client error: {error}"
        )

        return None