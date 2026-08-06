"""
Historial Service
Gestiona memoria conversacional Bitey.

Tabla actual:
messages
"""


from app.database.supabase import database



def get_messages(
    customer_id:int,
    company_id:int=1,
    limit:int=20
):

    try:


        result = (
            database
            .table("messages")
            .select("*")
            .eq(
                "customer_id",
                customer_id
            )
            .eq(
                "company_id",
                company_id
            )
            .order(
                "created_at",
                desc=True
            )
            .limit(limit)
            .execute()
        )


        return result.data or []



    except Exception as error:


        print(
            "[GET MESSAGES ERROR]",
            error
        )


        return []



# Compatibilidad Bitey V1-V15


def obtener_historial(
    customer_id,
    company_id=1,
    limit=20
):

    return get_messages(
        customer_id,
        company_id,
        limit
    )



def buscar_historial(
    customer_id,
    company_id=1,
    limit=20
):

    return get_messages(
        customer_id,
        company_id,
        limit
    )