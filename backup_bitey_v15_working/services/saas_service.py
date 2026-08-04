"""
BiteFixes SaaS Service

Handles Bitey AI SaaS products.

Supports:

- SaaS plans
- AI assistant subscriptions
- Business automation services
"""


from app.database.supabase import database



def get_saas_plans(
    company_id: int
):
    """
    Return available SaaS plans.
    """

    try:

        result = (
            database
            .table("saas_plans")
            .select("*")
            .eq(
                "company_id",
                company_id
            )
            .eq(
                "active",
                True
            )
            .execute()
        )


        return result.data or []


    except Exception as error:

        print(
            "[SAAS PLANS ERROR]",
            error
        )

        return []



def get_plan_by_id(
    plan_id: int
):
    """
    Return one SaaS plan.
    """

    try:

        result = (
            database
            .table("saas_plans")
            .select("*")
            .eq(
                "id",
                plan_id
            )
            .execute()
        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[SAAS PLAN ERROR]",
            error
        )

        return None



def create_subscription_request(
    company_id: int,
    customer_id: int,
    plan_id: int
):
    """
    Create SaaS subscription request.

    This is a commercial request.
    Payment integration comes later.
    """

    try:

        data = {

            "company_id": company_id,

            "customer_id": customer_id,

            "plan_id": plan_id,

            "status": "pending"

        }


        result = (
            database
            .table("subscriptions")
            .insert(data)
            .execute()
        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[SUBSCRIPTION CREATE ERROR]",
            error
        )

        return None



def get_customer_subscriptions(
    customer_id: int
):
    """
    Return customer SaaS subscriptions.
    """

    try:

        result = (
            database
            .table("subscriptions")
            .select("*")
            .eq(
                "customer_id",
                customer_id
            )
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )


        return result.data or []


    except Exception as error:

        print(
            "[CUSTOMER SUBSCRIPTIONS ERROR]",
            error
        )

        return []