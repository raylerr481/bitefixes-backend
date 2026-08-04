"""
Intent Repository

Database access layer for AI intents.

Responsibilities:
- Load active intents
- Get intent by name
- Manage company isolation

Multi-company SaaS ready.
"""

from app.database.supabase import supabase


DEFAULT_COMPANY_ID = 1


# =====================================================
# GET ALL ACTIVE INTENTS
# =====================================================

def get_all_active(
    company_id: int = DEFAULT_COMPANY_ID,
):

    try:

        result = (
            supabase
            .table("sinonimos_ia")
            .select("*")
            .eq(
                "empresa_id",
                company_id
            )
            .eq(
                "activo",
                True
            )
            .execute()
        )

        return result.data or []


    except Exception as error:

        print(
            f"[INTENT REPOSITORY] {error}"
        )

        return []



# =====================================================
# GET BY INTENT NAME
# =====================================================

def get_by_name(
    intent: str,
    company_id: int = DEFAULT_COMPANY_ID,
):

    try:

        result = (
            supabase
            .table("sinonimos_ia")
            .select("*")
            .eq(
                "empresa_id",
                company_id
            )
            .eq(
                "intent",
                intent
            )
            .eq(
                "activo",
                True
            )
            .limit(1)
            .execute()
        )


        if result.data:

            return result.data[0]


    except Exception as error:

        print(
            f"[INTENT REPOSITORY] {error}"
        )


    return None



# =====================================================
# GET BY SERVICE
# =====================================================

def get_by_service(
    service_id: int,
    company_id: int = DEFAULT_COMPANY_ID,
):

    try:

        result = (
            supabase
            .table("sinonimos_ia")
            .select("*")
            .eq(
                "empresa_id",
                company_id
            )
            .eq(
                "servicio_id",
                service_id
            )
            .eq(
                "activo",
                True
            )
            .execute()
        )


        return result.data or []


    except Exception as error:

        print(
            f"[INTENT REPOSITORY] {error}"
        )

        return []