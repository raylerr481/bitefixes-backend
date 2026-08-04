"""
BiteFixes Learning Service

Learns from previous conversations and AI logs.

Responsibilities:
- Customer profile
- Intent statistics
- Service recommendations
- Customer history
"""

from collections import Counter

from app.database.supabase import database



def get_customer_profile(customer_id: int):

    """
    Builds customer profile from messages.
    """

    try:

        result = (
            database
            .table("messages")
            .select("intent,service_id")
            .eq(
                "customer_id",
                customer_id
            )
            .execute()
        )


        messages = result.data or []


        intents = [

            m["intent"]

            for m in messages

            if m.get("intent")

        ]


        services = [

            m["service_id"]

            for m in messages

            if m.get("service_id")

        ]


        return {

            "total_messages":
                len(messages),


            "favorite_intent":
                Counter(intents)
                .most_common(1)[0][0]
                if intents else None,


            "favorite_service":
                Counter(services)
                .most_common(1)[0][0]
                if services else None

        }


    except Exception as error:

        print(
            "[LEARNING PROFILE ERROR]",
            error
        )

        return {}



def get_customer_statistics(customer_id: int):

    try:

        tickets = (
            database
            .table("tickets")
            .select("id,status")
            .eq(
                "customer_id",
                customer_id
            )
            .execute()
        )


        conversations = (
            database
            .table("conversations")
            .select("id")
            .eq(
                "customer_id",
                customer_id
            )
            .execute()
        )


        return {

            "tickets":
                len(
                    tickets.data or []
                ),


            "conversations":
                len(
                    conversations.data or []
                )

        }


    except Exception as error:

        print(
            "[LEARNING STATS ERROR]",
            error
        )

        return {}



def get_services_by_intent(
    intent: str,
    company_id: int
):

    """
    Returns services matching current detected intent.
    Current user need has priority over history.
    """


    if not intent:

        return []


    try:

        result = (

            database

            .table("services")

            .select("*")

            .eq(
                "intent",
                intent
            )

            .eq(
                "company_id",
                company_id
            )

            .eq(
                "is_active",
                True
            )

            .execute()

        )


        return result.data or []


    except Exception as error:

        print(
            "[SERVICE BY INTENT ERROR]",
            error
        )

        return []



def get_recommended_services(
    customer_id: int
):

    """
    Fallback recommendation based on customer history.
    """


    profile = get_customer_profile(
        customer_id
    )


    intent = profile.get(
        "favorite_intent"
    )


    if not intent:

        return []


    try:

        result = (

            database

            .table("services")

            .select("*")

            .eq(
                "intent",
                intent
            )

            .eq(
                "is_active",
                True
            )

            .execute()

        )


        return result.data or []


    except Exception as error:

        print(
            "[LEARNING RECOMMEND ERROR]",
            error
        )

        return []



def learn_from_ai_logs(company_id: int):

    try:

        logs = (

            database

            .table("ai_logs")

            .select(
                "detected_intent"
            )

            .eq(
                "company_id",
                company_id
            )

            .execute()

        )


        intents = [

            row["detected_intent"]

            for row in (logs.data or [])

            if row.get(
                "detected_intent"
            )

        ]


        return dict(
            Counter(intents)
        )


    except Exception as error:

        print(
            "[LEARNING AI LOG ERROR]",
            error
        )

        return {}