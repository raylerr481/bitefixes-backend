"""
Bitey Business Reasoning Layer V2

Resolves the semantic business chain:
Intent -> Need -> Requirements -> Solution -> Actions

Resolution is tenant-aware:
- tenant-specific definitions are preferred;
- global definitions are valid fallback definitions;
- operational company context remains separate from commercial plan limits.

This layer is read-only. It never executes actions or workflows.
"""

from typing import Any, Dict, List, Optional

from app.database.supabase import database


def _rows(table: str, company_id: int) -> List[Dict[str, Any]]:
    """Return active tenant-specific and global rows, preferring tenant data."""
    response = (
        database.table(table)
        .select("*")
        .or_(f"company_id.eq.{company_id},company_id.is.null")
        .execute()
    )
    rows = [row for row in (response.data or []) if row.get("is_active", True)]

    # A tenant definition overrides a global definition with the same code.
    by_code: Dict[str, Dict[str, Any]] = {}
    without_code: List[Dict[str, Any]] = []
    for row in rows:
        code = row.get("code")
        if not code:
            without_code.append(row)
            continue
        current = by_code.get(code)
        if current is None or (
            current.get("company_id") is None and row.get("company_id") == company_id
        ):
            by_code[code] = row
    return list(by_code.values()) + without_code


def _resolve_intent(company_id: int, intent_code: str) -> Optional[Dict[str, Any]]:
    rows = (
        database.table("intents")
        .select("*")
        .eq("code", intent_code)
        .eq("is_active", True)
        .or_(f"company_id.eq.{company_id},company_id.is.null")
        .execute()
    ).data or []

    tenant = [row for row in rows if row.get("company_id") == company_id]
    if tenant:
        return tenant[0]
    global_rows = [row for row in rows if row.get("company_id") is None]
    return global_rows[0] if global_rows else None


def _resolve_by_ids(rows: List[Dict[str, Any]], ids: set) -> List[Dict[str, Any]]:
    """Filter rows by relation IDs while preserving tenant/global precedence."""
    return [row for row in rows if row.get("id") in ids]


def resolve_business_reasoning(
    company_id: int,
    intent_code: Optional[str],
) -> Dict[str, Any]:
    """Resolve the complete semantic business path for a tenant and intent."""
    empty = {
        "intent": None,
        "needs": [],
        "requirements": [],
        "solutions": [],
        "actions": [],
        "reasoning_found": False,
    }

    if not company_id or not intent_code:
        return empty

    try:
        intent = _resolve_intent(company_id, intent_code)
        if not intent:
            return empty

        intent_id = intent.get("id")
        needs = [
            row for row in _rows("needs", company_id)
            if row.get("intent_id") == intent_id
        ]

        need_ids = {row.get("id") for row in needs}
        requirements = [
            row for row in _rows("requirements", company_id)
            if row.get("need_id") in need_ids
        ]

        solution_needs = (
            database.table("solution_needs")
            .select("*")
            .in_("need_id", list(need_ids) or [0])
            .execute()
        ).data or []
        solution_ids = {row.get("solution_id") for row in solution_needs}

        solutions = [
            row for row in _rows("solutions", company_id)
            if row.get("id") in solution_ids
        ]

        solution_actions = (
            database.table("solution_actions")
            .select("*")
            .in_("solution_id", list(solution_ids) or [0])
            .order("sequence_order")
            .execute()
        ).data or []
        action_ids = {row.get("action_id") for row in solution_actions}

        actions = [
            row for row in _rows("actions", company_id)
            if row.get("id") in action_ids
        ]

        return {
            "intent": intent,
            "needs": needs,
            "requirements": requirements,
            "solutions": solutions,
            "actions": actions,
            "reasoning_found": bool(needs or requirements or solutions or actions),
        }

    except Exception as error:
        print("[BUSINESS REASONING ERROR]", error)
        return empty
