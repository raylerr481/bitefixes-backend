"""
Bitey Business Reasoning Layer V2

Resolves the semantic business chain:
Intent -> Need -> Requirements -> Solution -> Actions

Company-specific definitions take precedence over global definitions. This
layer is read-only and deliberately does not enforce commercial plan limits.
"""

from typing import Any, Dict, List, Optional

from app.database.supabase import database


def _scoped_rows(table: str, company_id: int) -> List[Dict[str, Any]]:
    """Return global + company rows, preferring company-specific records."""
    response = (
        database.table(table)
        .select("*")
        .or_(f"company_id.eq.{company_id},company_id.is.null")
        .execute()
    )
    rows = response.data or []

    # A tenant override wins over a global definition with the same code.
    by_code: Dict[str, Dict[str, Any]] = {}
    without_code: List[Dict[str, Any]] = []
    for row in rows:
        code = row.get("code")
        if not code:
            without_code.append(row)
            continue
        current = by_code.get(code)
        if current is None or (
            current.get("company_id") is None
            and row.get("company_id") == company_id
        ):
            by_code[code] = row
    return list(by_code.values()) + without_code


def _find_intent(company_id: int, intent_code: str) -> Optional[Dict[str, Any]]:
    rows = (
        database.table("intents")
        .select("*")
        .eq("code", intent_code)
        .eq("is_active", True)
        .or_(f"company_id.eq.{company_id},company_id.is.null")
        .execute()
    ).data or []
    company_rows = [row for row in rows if row.get("company_id") == company_id]
    return (company_rows or rows or [None])[0]


def resolve_business_reasoning(
    company_id: int,
    intent_code: Optional[str],
) -> Dict[str, Any]:
    """Resolve the semantic business path for a tenant and intent."""
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
        intent = _find_intent(company_id, intent_code)
        if not intent:
            return empty

        needs = [
            row for row in _scoped_rows("needs", company_id)
            if row.get("intent_id") == intent.get("id")
            and row.get("is_active", True)
        ]

        need_ids = {need.get("id") for need in needs}
        requirements = [
            row for row in _scoped_rows("requirements", company_id)
            if row.get("need_id") in need_ids
        ]

        solutions_all = _scoped_rows("solutions", company_id)
        solution_needs = (
            database.table("solution_needs")
            .select("*")
            .in_("need_id", list(need_ids) or [0])
            .execute()
        ).data or []
        solution_ids = {row.get("solution_id") for row in solution_needs}

        solutions = [
            solution for solution in solutions_all
            if solution.get("id") in solution_ids
            and solution.get("is_active", True)
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
            action for action in _scoped_rows("actions", company_id)
            if action.get("id") in action_ids
            and action.get("is_active", True)
        ]

        return {
            "intent": intent,
            "needs": needs,
            "requirements": requirements,
            "solutions": solutions,
            "actions": actions,
            "reasoning_found": bool(needs or solutions or actions),
        }

    except Exception as error:
        print("[BUSINESS REASONING ERROR]", error)
        return empty
