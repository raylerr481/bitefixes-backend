"""
Bitey Service Resolver V10

Responsible for:

- Resolve service from detected intent
- Read services directly from Supabase
- Never use hardcoded SERVICE_MAP
"""

from typing import Optional, Dict

from app.database.supabase import database


def resolve_service(
    company_id: int,
    intent: Optional[str]
) -> Optional[Dict]:

    if not intent:
        return None

    try:

        response = (
            database
            .table("services")
            .select("*")
            .eq("company_id", company_id)
            .eq("intent", intent)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )

        if not response.data:

            print(
                "[SERVICE RESOLVER] No service for intent:",
                intent
            )

            return None

        service = response.data[0]

        print(
            "[SERVICE RESOLVER]",
            {
                "intent": intent,
                "service_id": service["id"],
                "service": service["name"]
            }
        )

        return service

    except Exception as error:

        print(
            "[SERVICE RESOLVER ERROR]",
            error
        )

        return None


def resolve_service_id(
    company_id: int,
    intent: Optional[str]
) -> Optional[int]:

    service = resolve_service(
        company_id,
        intent
    )

    if not service:
        return None

    return service["id"]


def resolve_service_name(
    company_id: int,
    intent: Optional[str]
) -> Optional[str]:

    service = resolve_service(
        company_id,
        intent
    )

    if not service:
        return None

    return service["name"]