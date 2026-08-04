"""
Knowledge Repository

Database access layer for company knowledge.

Responsibilities:
- Search knowledge
- Get knowledge by intent
- Get knowledge by service
- List active knowledge

Multi-company SaaS ready.
"""

from app.database.supabase import supabase


DEFAULT_COMPANY_ID = 1


# =====================================================
# SEARCH ALL ACTIVE KNOWLEDGE
# =====================================================

def get_all_active(
    company_id: int = DEFAULT_COMPANY_ID,
):

    result = (
        supabase
        .table("base_conhecimento")
        .select("*")
        .eq("empresa_id", company_id)
        .eq("activo", True)
        .order(
            "prioridad",
            desc=True
        )
        .execute()
    )

    return result.data or []


# =====================================================
# GET BY INTENT
# =====================================================

def get_by_intent(
    intent: str,
    company_id: int = DEFAULT_COMPANY_ID,
):

    result = (
        supabase
        .table("base_conhecimento")
        .select("*")
        .eq("empresa_id", company_id)
        .eq("activo", True)
        .eq(
            "intencion",
            intent
        )
        .order(
            "prioridad",
            desc=True
        )
        .limit(1)
        .execute()
    )

    if result.data:

        return result.data[0]

    return None


# =====================================================
# GET BY SERVICE
# =====================================================

def get_by_service(
    service_id: int,
    company_id: int = DEFAULT_COMPANY_ID,
):

    result = (
        supabase
        .table("base_conhecimento")
        .select("*")
        .eq("empresa_id", company_id)
        .eq("activo", True)
        .eq(
            "servicio_id",
            service_id
        )
        .order(
            "prioridad",
            desc=True
        )
        .execute()
    )

    return result.data or []


# =====================================================
# SEARCH BY WORD
# =====================================================

def search_text(
    text: str,
    company_id: int = DEFAULT_COMPANY_ID,
):

    result = (
        supabase
        .table("base_conhecimento")
        .select("*")
        .eq("empresa_id", company_id)
        .eq("activo", True)
        .execute()
    )

    rows = result.data or []

    matches = []

    text = text.lower()

    for row in rows:

        content = " ".join(
            [
                str(row.get("titulo", "")),
                str(row.get("pregunta", "")),
                str(row.get("tags", "")),
            ]
        ).lower()

        if text in content:

            matches.append(row)

    return matches