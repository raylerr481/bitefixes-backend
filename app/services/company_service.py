"""Bitey Company Context Service V5.

The Company AI Profile is the authoritative tenant identity/context layer.
Legacy business tables remain available as supporting structured context.
"""
from typing import Any, Dict, List, Optional
from app.database.supabase import database


def _rows(table: str, **filters: Any) -> List[Dict[str, Any]]:
    query = database.table(table).select("*")
    for column, value in filters.items():
        if value is not None:
            query = query.eq(column, value)
    response = query.execute()
    return response.data or []


def get_company(company_id: int) -> Optional[Dict[str, Any]]:
    rows = _rows("companies", id=company_id)
    return rows[0] if rows else None


def get_company_ai_profile(company_id: int) -> Optional[Dict[str, Any]]:
    """Return the authoritative Company AI Profile for one tenant."""
    rows = _rows("company_ai_profiles", company_id=company_id)
    if not rows:
        return None
    row = rows[0]
    profile = row.get("profile")
    if not isinstance(profile, dict):
        profile = {}
    return {
        "id": row.get("id"),
        "company_id": row.get("company_id"),
        "company_name": row.get("company_name"),
        "description": row.get("description"),
        "industry": row.get("industry"),
        "profile": profile,
        "updated_at": row.get("updated_at"),
        "authoritative": True,
    }


def get_business_profile(company_id: int) -> Optional[Dict[str, Any]]:
    rows = _rows("business_profiles", company_id=company_id)
    return rows[0] if rows else None


def get_industries(company_id: int) -> List[Dict[str, Any]]:
    profiles = _rows("business_profiles", company_id=company_id)
    profile_ids = {p.get("id") for p in profiles}
    relations = [r for r in _rows("business_profile_industries") if r.get("business_profile_id") in profile_ids]
    lookup = {r.get("id"): r for r in _rows("industries")}
    return [{"industry": lookup[r["industry_id"]], "is_primary": r.get("is_primary"), "confidence": r.get("confidence")} for r in relations if r.get("industry_id") in lookup]


def get_business_models(company_id: int) -> List[Dict[str, Any]]:
    profiles = _rows("business_profiles", company_id=company_id)
    profile_ids = {p.get("id") for p in profiles}
    relations = [r for r in _rows("business_profile_models") if r.get("business_profile_id") in profile_ids]
    lookup = {r.get("id"): r for r in _rows("business_models")}
    return [lookup[r["business_model_id"]] for r in relations if r.get("business_model_id") in lookup]


def get_business_functions(company_id: int) -> List[Dict[str, Any]]:
    relations = [r for r in _rows("company_business_functions", company_id=company_id) if r.get("enabled", True)]
    lookup = {r.get("id"): r for r in _rows("business_functions")}
    result = []
    for relation in relations:
        function = lookup.get(relation.get("function_id"))
        if function:
            result.append({"function": function, "priority": relation.get("priority", 0), "metadata": relation.get("metadata") or {}})
    return sorted(result, key=lambda item: item["priority"])


def get_subscription_context(company_id: int) -> Optional[Dict[str, Any]]:
    subscriptions = _rows("subscriptions", company_id=company_id)
    if not subscriptions:
        return None
    active = [r for r in subscriptions if r.get("status") == "active"]
    subscription = active[0] if active else subscriptions[0]
    plan = None
    if subscription.get("plan_id") is not None:
        rows = _rows("plans", id=subscription["plan_id"])
        plan = rows[0] if rows else None
    return {"subscription": subscription, "plan": plan}


def get_ai_scope(company_id: int) -> Optional[Dict[str, Any]]:
    rows = _rows("ai_scopes", company_id=company_id)
    return rows[0] if rows else None


def get_company_domains(company_id: int) -> List[Dict[str, Any]]:
    relations = _rows("company_domains", company_id=company_id)
    lookup = {r.get("id"): r for r in _rows("business_domains")}
    return [{"domain": lookup[r["domain_id"]], "relevance": r.get("relevance"), "metadata": r.get("metadata") or {}} for r in relations if r.get("domain_id") in lookup]


def get_company_capabilities(company_id: int) -> List[Dict[str, Any]]:
    relations = [r for r in _rows("company_capabilities", company_id=company_id) if r.get("enabled", True)]
    lookup = {r.get("id"): r for r in _rows("capabilities")}
    result = []
    for relation in relations:
        function = lookup.get(relation.get("capability_id"))
        if function:
            result.append({"capability": function, "source": relation.get("source"), "metadata": relation.get("metadata") or {}})
    return result


def get_company_services(company_id: int) -> List[Dict[str, Any]]:
    return _rows("services", company_id=company_id, is_active=True)


def get_company_locations(company_id: int) -> List[Dict[str, Any]]:
    """Return active company locations for routing/location questions."""
    return _rows("company_locations", company_id=company_id, is_active=True)


def get_company_knowledge(company_id: int) -> List[Dict[str, Any]]:
    return _rows("knowledge_base", company_id=company_id, is_active=True)


def _is_bitefixes_identity(company: Dict[str, Any], ai_profile: Optional[Dict[str, Any]]) -> bool:
    """Limit the built-in service addition to the BiteFixes tenant only."""
    names = [
        company.get("name", ""),
        (ai_profile or {}).get("company_name", ""),
    ]
    return any("bitefixes" in str(name).casefold() for name in names)


def _has_printer_service(services: List[Dict[str, Any]]) -> bool:
    """Avoid duplicating an existing active printer service."""
    terms = ("impresora", "printer", "impressora", "printing", "print repair")
    for service in services:
        searchable = " ".join(
            str(service.get(key) or "")
            for key in ("name", "title", "service_name", "description", "category", "slug")
        ).casefold()
        if any(term in searchable for term in terms):
            return True
    return False


def _include_bitefixes_printer_service(
    company_id: int,
    company: Dict[str, Any],
    ai_profile: Optional[Dict[str, Any]],
    services: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Ensure the AI context knows printer repair is a BiteFixes service.

    This is an application-level catalog entry: it does not write to Supabase
    or alter existing tables. A persistent CRM service record can be added
    separately after confirming the live schema and current catalog.
    """
    if not _is_bitefixes_identity(company, ai_profile) or _has_printer_service(services):
        return services

    return [
        *services,
        {
            "id": None,
            "company_id": company_id,
            "name": "Printer repair and maintenance",
            "service_name": "Printer repair and maintenance",
            "slug": "printer-repair-maintenance",
            "category": "hardware_repair",
            "description": (
                "Repair and maintenance of inkjet and laser printers; diagnosis of "
                "paper jams, print-quality issues, ink or toner problems, error messages, "
                "driver installation, USB and Wi-Fi connectivity, and configuration."
            ),
            "is_active": True,
            "source": "built_in_bitefixes_service_catalog",
            "languages": ["es", "pt-BR", "en"],
            "customer_intake": ["brand", "model", "symptoms", "error_message"],
        },
    ]


def get_company_context(company_id: int) -> Dict[str, Any]:
    company = get_company(company_id)
    if not company:
        return {
            "company": None,
            "company_id": company_id,
            "company_name": None,
            "company_ai_profile": None,
            "business_profile": None,
            "industries": [],
            "business_models": [],
            "business_functions": [],
            "subscription": None,
            "ai_scope": None,
            "domains": [],
            "capabilities": [],
            "services": [],
            "locations": [],
            "knowledge": [],
        }

    business_profile = get_business_profile(company_id)
    ai_profile = get_company_ai_profile(company_id)
    profile_data = (ai_profile or {}).get("profile") or {}
    services = get_company_services(company_id)
    services = _include_bitefixes_printer_service(company_id, company, ai_profile, services)
    directives = {**(profile_data.get("behavior") or {}), **(profile_data.get("governance") or {})}
    if _is_bitefixes_identity(company, ai_profile):
        directives["service_catalog_rule"] = (
            "BiteFixes offers printer repair and maintenance. For questions in Spanish or Portuguese "
            "about repairing printers (impresoras/impressoras), confirm that the service is offered, "
            "then ask for the printer brand, model, and symptoms or error message. Do not say printer "
            "repair is not listed or unavailable. Do not promise a price, turnaround, or repair outcome "
            "without verification."
        )

    return {
        "company": company,
        "company_id": company_id,
        "company_name": ai_profile.get("company_name") if ai_profile else company.get("name"),
        "company_ai_profile": ai_profile,
        "business_profile": business_profile,
        "industries": get_industries(company_id),
        "business_models": get_business_models(company_id),
        "business_functions": get_business_functions(company_id),
        "subscription": get_subscription_context(company_id),
        "ai_scope": get_ai_scope(company_id),
        "domains": get_company_domains(company_id),
        "capabilities": get_company_capabilities(company_id),
        "services": services,
        "locations": get_company_locations(company_id),
        "knowledge": get_company_knowledge(company_id),
        "objectives": profile_data.get("objectives") or (business_profile or {}).get("objective") or [],
        "directives": directives,
        "profile_authoritative": bool(ai_profile and ai_profile.get("authoritative")),
    }
