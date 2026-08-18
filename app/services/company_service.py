"""Bitey Company Context Service V4."""
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
    return [{"capability": lookup[r["capability_id"]], "source": r.get("source"), "metadata": r.get("metadata") or {}} for r in relations if r.get("capability_id") in lookup]


def get_company_services(company_id: int) -> List[Dict[str, Any]]:
    return _rows("services", company_id=company_id, is_active=True)


def get_company_knowledge(company_id: int) -> List[Dict[str, Any]]:
    return _rows("knowledge_base", company_id=company_id, is_active=True)


def get_company_context(company_id: int) -> Dict[str, Any]:
    company = get_company(company_id)
    if not company:
        return {"company": None, "business_profile": None, "industries": [], "business_models": [], "business_functions": [], "subscription": None, "ai_scope": None, "domains": [], "capabilities": [], "services": [], "knowledge": []}
    return {
        "company": company,
        "business_profile": get_business_profile(company_id),
        "industries": get_industries(company_id),
        "business_models": get_business_models(company_id),
        "business_functions": get_business_functions(company_id),
        "subscription": get_subscription_context(company_id),
        "ai_scope": get_ai_scope(company_id),
        "domains": get_company_domains(company_id),
        "capabilities": get_company_capabilities(company_id),
        "services": get_company_services(company_id),
        "knowledge": get_company_knowledge(company_id),
    }
