"""
Customer Service

Handles customer creation,
retrieval and updates.
"""

from app.database.supabase import database


def get_customer(
    company_id: int,
    phone: str
):
    """
    Returns a customer by phone.
    """

    result = (
        database
        .table("customers")
        .select("*")
        .eq("company_id", company_id)
        .eq("phone", phone)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None



def create_customer(
    company_id: int,
    phone: str,
    full_name: str = "Customer"
):
    """
    Creates a new customer.
    """

    data = {
        "company_id": company_id,
        "phone": phone,
        "full_name": full_name
    }

    result = (
        database
        .table("customers")
        .insert(data)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None



def update_customer(
    customer_id: int,
    data: dict
):
    """
    Updates customer information.
    """

    result = (
        database
        .table("customers")
        .update(data)
        .eq("id", customer_id)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None



def get_or_create_customer(
    company_id: int,
    phone: str,
    full_name: str = "Customer"
):
    """
    Retrieves existing customer
    or creates a new one.
    """

    try:

        customer = get_customer(
            company_id,
            phone
        )

        if customer:

            if (
                full_name
                and full_name != customer.get("full_name")
            ):

                customer = update_customer(
                    customer["id"],
                    {
                        "full_name": full_name
                    }
                )

            return customer


        return create_customer(
            company_id,
            phone,
            full_name
        )


    except Exception as error:

        print(
            "[CUSTOMER SERVICE ERROR]",
            error
        )

        raise



def get_or_create_customer_by_phone(
    company_id: int,
    phone: str,
    name: str = None
):
    """
    Compatibility alias.
    """

    return get_or_create_customer(
        company_id=company_id,
        phone=phone,
        full_name=name or "Customer"
    )



def get_customer_by_whatsapp(
    company_id: int,
    whatsapp: str
):
    """
    Compatibility alias.
    """

    return get_customer(
        company_id,
        whatsapp
    )