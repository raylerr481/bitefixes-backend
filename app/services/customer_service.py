"""
Customer Service

Responsible for customer management.

Supports:

- Website customers
- WhatsApp customers
- Mobile App customers
- Other channels

Architecture:
Customer identified by company + phone
"""

from datetime import datetime

from app.database.supabase import database



# =====================================================
# GET CUSTOMER BY PHONE
# =====================================================

def get_customer_by_phone(
    phone: str,
    company_id: int = 1
):

    try:

        if not phone:
            return None


        result = (

            database

            .table("customers")

            .select("*")

            .eq(
                "company_id",
                company_id
            )

            .eq(
                "phone",
                phone
            )

            .execute()

        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[CUSTOMER LOOKUP ERROR]",
            error
        )

        return None



# =====================================================
# CREATE CUSTOMER
# =====================================================

def create_customer(

    company_id: int,

    phone: str,

    name: str = "Customer"

):

    try:


        customer = {


            "company_id":

                company_id,


            "full_name":

                name,


            "phone":

                phone,


            "preferred_language":

                "pt-BR",


            "customer_type":

                "individual",


            "is_active":

                True,


            "last_access":

                datetime.utcnow().isoformat()

        }



        result = (

            database

            .table("customers")

            .insert(customer)

            .execute()

        )


        if result.data:

            return result.data[0]


        return None



    except Exception as error:


        print(

            "[CUSTOMER CREATE ERROR]",

            error

        )


        return None



# =====================================================
# GET OR CREATE CUSTOMER
# =====================================================

def get_or_create_customer(

    company_id: int,

    phone: str,

    name: str = "Customer"

):


    customer = get_customer_by_phone(

        phone,

        company_id

    )


    if customer:


        return customer



    return create_customer(

        company_id,

        phone,

        name

    )
# =====================================================
# COMPATIBILITY ALIAS
# =====================================================

def get_customer_by_whatsapp(
    whatsapp: str,
    company_id: int = 1
):

    return get_customer_by_phone(
        whatsapp,
        company_id
    )
# =====================================================
# GET CUSTOMER BY CHANNEL
# =====================================================

def get_customer_by_channel(
    channel: str,
    value: str,
    company_id: int = 1
):

    """
    Find customer by communication channel.

    Supported channels:

    - whatsapp
    - phone
    """

    if not value:
        return None


    channel = channel.lower()


    if channel in [
        "whatsapp",
        "phone"
    ]:

        return get_customer_by_phone(
            value,
            company_id
        )


    return None