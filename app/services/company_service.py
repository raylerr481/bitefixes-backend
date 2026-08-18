"""
Bitey Company Context Service V3
================================

Builds the normalized business context used by Bitey.

Architecture:
    Company
      -> Business Profile
      -> Subscription / Plan
      -> AI Scope
      -> Business Domains
      -> Capabilities
      -> Services
      -> Knowledge

This service is intentionally read-only. It does not create tickets,
messages, workflows, or business records.

Compatibility:
    Existing services and knowledge_base records remain the operational
    source of truth while the new Bitey V22 business-context model is
    progressively populated.
"""

from typing import Any, Dict, List, Optional

from app.database.supabase import database



def _rows(table: str, **filters: Any) -> List[Dict[str, Any]]:
    """Return active/related rows without raising when the collection is empty."""
    query = database.table(table).select("*")

    for column, value in filters.items():
        if value is not None:
            query = query.eq(column, value)

    response = query.execute()
    return response.data or []



def get_company(company_id: int) -> Optional[Dict[str, Any]]:
    """Return the company record."""
    rows = _rows("companies", id=company_id)
    return rows[0] if rows else None



def get_business_profile(company_id: int) -> Optional[Dict[str, Any]]:
    """Return the normalized business profile, when configured."""
    rows = _rows("business_profiles", company_id=company_id)
    return rows[0] if rows else None



def get_subscription_context(company_id: int) -> Optional[Dict[str, Any]]:
    """Return the current subscription together with its plan."""
    subscriptions = _rows("subscriptions", company_id=company_id)

    if not subscriptions:
        return None

    # Prefer an active subscription; otherwise use the most recent record.
    active = [row for row in subscriptions if row.get("status") == "active"]
    subscription = active[0] if active else subscriptions[0]

    plan_id = subscription.get("plan_id")
    plan = None

    if plan_id is not None:
        plans = _rows("plans", id=plan_id)
        plan = plans[0] if plans else None

    return {
        "subscription": subscription,
        "plan": plan,
    }



def get_ai_scope(company_id: int) -> Optional[Dict[str, Any]]:
    """Return the company's AI policy/scope configuration."""
    rows = _rows("ai_scopes", company_id=company_id)
    return rows[0] if rows else None



def get_company_domains(company_id: int) -> List[Dict[str, Any]]:
    """Return domains assigned to the company with their relevance metadata."""
    relations = _rows("company_domains", company_id=company_id)

    if not relations:
        return []

    domain_ids = [row.get("domain_id") for row in relations if row.get("domain_id")]
    if not domain_ids:
        return []

    domains = _rows("business_domains")
    domain_map = {row.get("id"): row for row in domains}

    result = []
    for relation in relations:
        domain = domain_map.get(relation.get("domain_id"))
        if domain:
            result.append({
                "domain": domain,
                "relevance": relation.get("relevance"),
                "metadata": relation.get("metadata") or {},
            })

    return result



def get_company_capabilities(company_id: int) -> List[Dict[str, Any]]:
    """Return enabled capabilities assigned to the company."""
    relations = _rows("company_capabilities", company_id=company_id)
    relations = [row for row in relations if row.get("enabled", True)]

    if not relations:
        return []

    capabilities = _rows("capabilities")
    capability_map = {row.get("id"): row for row in capabilities}

    result = []
    for relation in relations:
        capability = capability_map.get(relation.get("capability_id"))
        if capability:
            result.append({
                "capability": capability,
                "source": relation.get("source"),
                "metadata": relation.get("metadata") or {},
            })

    return result



def get_company_services(company_id: int) -> List[Dict[str, Any]]:
    """Return the company's active operational services."""
    return _rows("services", company_id=company_id, is_active=True)



def get_company_knowledge(company_id: int) -> List[Dict[str, Any]]:
    """Return active knowledge records for the company."""
    return _rows("knowledge_base", company_id=company_id, is_active=True)



def get_company_context(company_id: int) -> Dict[str, Any]:
    """
    Build the canonical business context consumed by Bitey.

    The old service/knowledge records are deliberately preserved so the
    migration can be incremental. New business intelligence is exposed
    through the V22 entities instead of being hidden inside workflow state.
    """
    company = get_company(company_id)

    if not company:
        return {
            "company": None,
            "business_profile": None,
            "subscription": None,
            "ai_scope": None,
            "domains": [],
            "capabilities": [],
            "services": [],
            "knowledge": [],
        }

    subscription = get_subscription_context(company_id)

    return {
        "company": company,
        "business_profile": get_business_profile(company_id),
        "subscription": subscription,
        "ai_scope": get_ai_scope(company_id),
        "domains": get_company_domains(company_id),
        "capabilities": get_company_capabilities(company_id),
        "services": get_company_services(company_id),
        "knowledge": get_company_knowledge(company_id),
    }
