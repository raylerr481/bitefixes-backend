"""
Cliente Service
Gestiona clientes desde Supabase.
Tabla actual:
customers
"""


from app.database.supabase import database



def get_customer(
    customer_id: int,
    company_id: int = 1
):

    try:

        result = (
            database
            .table("customers")
            .select("*")
            .eq(
                "id",
                customer_id
            )
            .eq(
                "company_id",
                company_id
            )
            .limit(1)
            .execute()
        )


        if result.data:
            return result.data[0]


        return None


    except Exception as error:

        print(
            "[GET CUSTOMER ERROR]",
            error
        )

        return None



# Compatibilidad versiones anteriores Bitey

def buscar_cliente(
    customer_id,
    company_id=1
):

    return get_customer(
        customer_id,
        company_id
    )



def obtener_cliente(
    customer_id,
    company_id=1
):

    return get_customer(
        customer_id,
        company_id
    )