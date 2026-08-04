"""
BiteFixes Lead Service V4

CRM commercial opportunity manager.

Responsible for:
- Creating leads
- Avoiding duplicates
- Lead scoring
- Pipeline stages
- Commercial tracking

Database:
Supabase

Table:
leads
"""


from datetime import datetime

from app.supabase_client import supabase



TABLE = "leads"



# =====================================================
# FIND OPEN LEAD
# =====================================================


def get_open_lead(
    customer_id:int,
    intent:str
):

    try:


        result = (

            supabase
            .table(TABLE)
            .select("*")
            .eq(
                "customer_id",
                customer_id
            )
            .eq(
                "intent",
                intent
            )
            .neq(
                "status",
                "closed"
            )
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




# =====================================================
# SCORE CALCULATOR
# =====================================================


def calculate_lead_score(
    intent:str
):


    high_value = [

        "website_creation",

        "ai_assistant",

        "mobile_app",

        "crm",

        "automation"

    ]


    medium_value = [

        "computer_repair",

        "network_configuration",

        "cctv_installation"

    ]



    if intent in high_value:

        return 80



    if intent in medium_value:

        return 50



    return 20




# =====================================================
# CREATE LEAD
# =====================================================


def create_lead(
    company_id:int,
    customer_id:int,
    intent:str,
    service_id:int=None,
    stage:str="discovery",
    score:int=None,
    notes:str=None
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




        if score is None:

            score = calculate_lead_score(
                intent
            )




        data = {


            "company_id":
                company_id,


            "customer_id":
                customer_id,


            "service_id":
                service_id,


            "intent":
                intent,


            "stage":
                stage,


            "score":
                score,


            "status":
                "new",


            "notes":
                notes,


            "created_at":
                datetime.utcnow()
                .isoformat()



        }



        result = (

            supabase
            .table(TABLE)
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




# =====================================================
# GET LEAD
# =====================================================


def get_lead(
    lead_id:int
):


    try:


        result = (

            supabase
            .table(TABLE)
            .select("*")
            .eq(
                "id",
                lead_id
            )
            .limit(1)
            .execute()

        )


        if result.data:

            return result.data[0]


        return None



    except Exception as error:


        print(
            "[LEAD GET ERROR]",
            error
        )


        return None




# =====================================================
# CUSTOMER LEADS
# =====================================================


def get_customer_leads(
    customer_id:int
):


    try:


        result = (

            supabase
            .table(TABLE)
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




# =====================================================
# UPDATE LEAD
# =====================================================


def update_lead(
    lead_id:int,
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



        data["updated_at"] = (
            datetime.utcnow()
            .isoformat()
        )



        result = (

            supabase
            .table(TABLE)
            .update(data)
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
            "[LEAD UPDATE ERROR]",
            error
        )


        return None




# =====================================================
# CLOSE LEAD
# =====================================================


def close_lead(
    lead_id:int
):


    return update_lead(

        lead_id,

        status="closed"

    )