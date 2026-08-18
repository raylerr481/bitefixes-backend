"""
Bitey Service Resolver V11
==========================

Resolve an operational service from company context and intent.

Resolution order:
    1. Active company service explicitly mapped to the detected intent.
    2. Active company service mapped to the relevant capability.
    3. Legacy intent-only company service lookup.

The resolver does not decide whether an intent is allowed. AI Scope policy
belongs to the decision engine; this module resolves operational capabilities.
"""

from typing import Any, Dict, Optional

from app.database.supabase import database


def _active_services(company_id: int):
    response = (
        database.table("services")
        .select("*")
        .eq("company_id", company_id)
        .eq("is_active", True)
        .execute()
    )
    return response.data or []


def _capability_ids(context: Optional[Dict[str, Any]], intent: Optional[str]):
    """Extract enabled capability IDs from the already-loaded V22 context."""
    if not context:
        return []

    ids = []
    for item in context.get("capabilities") or []:
        capability = item.get("capability") or {}
        if capability.get("id") is not None:
            ids.append(capability["id"])

    # Context is authoritative; intent remains the operational fallback.
    return ids


def resolve_service(
    company_id: int,
    intent: Optional[str],
    business_context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Resolve the best active operational service for a company request."""
    if not intent:
        return None

    try:
        services = _active_services(company_id)

        # 1. Exact intent match remains the strongest signal.
        exact = [service for service in services if service.get("intent") == intent]
        if exact:
            return exact[0]

        # 2. Use the contextual capability graph when available.
        capability_ids = set(_capability_ids(business_context, intent))
        if capability_ids:
            contextual = [
                service
                for service in services
                if service.get("capability_id") in capability_ids
            ]
            if contextual:
                return contextual[0]

        # 3. Legacy behavior: no contextual mapping means no fabricated service.
        print("[SERVICE RESOLVER] No contextual service for intent:", intent)
        return None

    except Exception as error:
        print("[SERVICE RESOLVER ERROR]", error)
        return None


def resolve_service_id(
    company_id: int,
    intent: Optional[str],
    business_context: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    service = resolve_service(company_id, intent, business_context)
    return service.get("id") if service else None


def resolve_service_name(
    company_id: int,
    intent: Optional[str],
    business_context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    service = resolve_service(company_id, intent, business_context)
    return service.get("name") if service else None
