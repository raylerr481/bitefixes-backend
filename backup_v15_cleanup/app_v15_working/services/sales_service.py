"""
BiteFixes Sales Service

Handles commercial opportunities.

Supports:

- Product sales leads
- SaaS leads
- Customer requests
- Sales tracking
"""

from app.database.supabase import database



def create_sales_lead(
    company_id: int,
    customer_id: int,
    interest: str,
    description: str = None,
    source: str = "website"
):
    """
    Create a new sales opportunity.
    """

    try:

        data = {

            "company_id": company_id,

            "customer_id": customer_id,

            "interest": interest,

            "description": description,

            "source": source,

            "status": "new"

        }


        result = (
            database
            .table("sales_leads")
            .insert(data)
            .execute()
        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[SALES LEAD CREATE ERROR]",
            error
        )

        return None



def get_customer_sales_leads(
    customer_id: int
):
    """
    Return customer sales history.
    """

    try:

        result = (
            database
            .table("sales_leads")
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
            "[SALES LEADS ERROR]",
            error
        )

        return []



def update_sales_lead_status(
    lead_id: int,
    status: str
):
    """
    Update sales opportunity status.

    Examples:

    new
    contacted
    quoted
    sold
    cancelled

    """

    try:

        result = (
            database
            .table("sales_leads")
            .update(
                {
                    "status": status
                }
            )
            .eq(
                "id",
                lead_id
            )
            .execute()
        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[SALES UPDATE ERROR]",
            error
        )

        return None