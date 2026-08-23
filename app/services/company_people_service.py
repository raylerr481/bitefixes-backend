"""Company people and role context for Bitey's enterprise profile."""

from __future__ import annotations

from typing import Any

from app.database.supabase import database


ACTIVE_ROLE_CODES = {
    "owner",
    "founder",
    "partner",
    "legal_representative",
    "representative",
    "director",
    "manager",
    "administrator",
    "supervisor",
    "employee",
    "sales",
    "sales_manager",
    "technical",
    "technical_lead",
    "support",
    "customer_service",
    "finance",
    "accounting",
    "hr",
    "marketing",
    "it",
    "security",
    "logistics",
    "procurement",
    "contractor",
    "consultant",
    "supplier_contact",
    "customer_contact",
    "other",
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def list_company_people(company_id: int, *, active_only: bool = True) -> list[dict]:
    """Return company people with their active roles."""
    query = (
        database.table("company_people")
        .select("*")
        .eq("company_id", int(company_id))
    )
    if active_only:
        query = query.eq("is_active", True)

    people = query.order("full_name").execute().data or []
    if not people:
        return []

    person_ids = [row["id"] for row in people if row.get("id") is not None]
    roles = (
        database.table("company_person_roles")
        .select("*")
        .in_("company_person_id", person_ids)
        .eq("is_active", True)
        .execute()
        .data
        or []
    )

    grouped: dict[int, list[dict]] = {}
    for role in roles:
        grouped.setdefault(int(role["company_person_id"]), []).append(role)

    for person in people:
        person["roles"] = grouped.get(int(person["id"]), [])

    return people


def build_company_people_context(company_id: int, *, active_only: bool = True) -> dict:
    """Build a compact, non-sensitive people context for enterprise AI."""
    people = list_company_people(company_id, active_only=active_only)

    context = []
    for person in people:
        roles = [
            {
                "code": role.get("role_code"),
                "name": role.get("role_name") or role.get("role_code"),
                "primary": bool(role.get("is_primary")),
                "authority_level": int(role.get("authority_level") or 0),
            }
            for role in person.get("roles", [])
        ]

        context.append(
            {
                "id": person.get("id"),
                "name": person.get("full_name"),
                "job_title": person.get("job_title"),
                "department": person.get("department"),
                "person_type": person.get("person_type"),
                "roles": roles,
                "is_primary": bool(person.get("is_primary")),
                "ai_context_authority": bool(person.get("ai_context_authority")),
                "can_be_contacted_by_ai": bool(person.get("can_be_contacted_by_ai")),
                "preferred_language": person.get("preferred_language"),
                "preferred_channel": person.get("preferred_channel"),
            }
        )

    return {"company_people": context, "count": len(context)}


def find_company_people_by_role(
    company_id: int,
    role_code: str,
    *,
    active_only: bool = True,
) -> list[dict]:
    """Find people assigned to a specific company role."""
    role_code = _clean(role_code).lower()
    if role_code not in ACTIVE_ROLE_CODES:
        return []

    roles_query = (
        database.table("company_person_roles")
        .select("company_person_id")
        .eq("role_code", role_code)
        .eq("is_active", True)
    )
    role_rows = roles_query.execute().data or []
    person_ids = [row["company_person_id"] for row in role_rows]
    if not person_ids:
        return []

    people_query = (
        database.table("company_people")
        .select("*")
        .eq("company_id", int(company_id))
        .in_("id", person_ids)
    )
    if active_only:
        people_query = people_query.eq("is_active", True)

    return people_query.order("full_name").execute().data or []
