"""
BiteFixes Lead Service V3
Handles commercial opportunities.
Avoids duplicate leads.
"""

from app.supabase_client import supabase


def get_open_lead(customer_id, intent):

    try:

        result = (
            supabase
            .table("leads")
            .select("*")
            .eq("customer_id", customer_id)
            .eq("intent", intent)
            .neq("status", "closed")
            .execute()
        )

        if result.data:
            return result.data[0]

        return None


    except Exception as error:

        print(
            "[LEAD SEARCH ERROR]",
            error
        )

        return None



def create_lead(
    company_id,
    customer_id,
    intent,
    service_id=None,
    stage="discovery",
    score=0,
    notes=None
):

    try:

        existing = get_open_lead(
            customer_id,
            intent
        )


        if existing:

            print(
                "[LEAD EXISTING]",
                existing["id"]
            )

            return existing



        data = {

            "company_id": company_id,
            "customer_id": customer_id,
            "service_id": service_id,
            "intent": intent,
            "stage": stage,
            "score": score,
            "status": "new",
            "notes": notes

        }


        result = (
            supabase
            .table("leads")
            .insert(data)
            .execute()
        )


        if result.data:

            print(
                "[LEAD CREATED]",
                result.data[0]["id"]
            )

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[LEAD CREATE ERROR]",
            error
        )

        return None



def get_customer_leads(customer_id):

    try:

        result = (
            supabase
            .table("leads")
            .select("*")
            .eq(
                "customer_id",
                customer_id
            )
            .execute()
        )


        return result.data or []


    except Exception as error:

        print(
            "[LEAD LIST ERROR]",
            error
        )

        return []



def update_lead(
    lead_id,
    stage=None,
    score=None,
    notes=None,
    status=None
):

    try:

        data = {}


        if stage is not None:
            data["stage"] = stage


        if score is not None:
            data["score"] = score


        if notes is not None:
            data["notes"] = notes


        if status is not None:
            data["status"] = status



        if not data:

            return None



        result = (
            supabase
            .table("leads")
            .update(data)
            .eq(
                "id",
                lead_id
            )
            .execute()
        )


        if result.data:

            print(
                "[LEAD UPDATED]",
                lead_id
            )

            return result.data[0]


        return None



    except Exception as error:

        print(
            "[LEAD UPDATE ERROR]",
            error
        )

        return None