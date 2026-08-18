"""
Bitey Business Reasoning Layer V3

Resolves:
Intent -> Need -> Requirements -> Solution -> Actions

This layer is read-only. It does not execute workflows or actions.
"""

from typing import Any, Dict, List, Optional

from app.database.supabase import database


def _rows(table: str, company_id: int) -> List[Dict[str, Any]]:
    response = (
        database.table(table)
        .select("*")
        .or_(f"company_id.eq.{company_id},company_id.is.null")
        .execute()
    )
    rows = [row for row in (response.data or []) if row.get("is_active", True)]

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


def resolve_business_reasoning(company_id: int, intent_code: Optional[str]) -> Dict[str, Any]:
    empty = {
        "intent": None,
        "needs": [],
        "requirements": [],
        "solutions": [],
        "actions": [],
        "next_step": None,
        "reasoning_found": False,
    }
    if not company_id or not intent_code:
        return empty

    try:
        intent = _resolve_intent(company_id, intent_code)
        if not intent:
            return empty

        needs = [r for r in _rows("needs", company_id) if r.get("intent_id") == intent.get("id")]
        need_ids = {r.get("id") for r in needs}
        requirements = [r for r in _rows("requirements", company_id) if r.get("need_id") in need_ids]

        solution_needs = (
            database.table("solution_needs")
            .select("*")
            .in_("need_id", list(need_ids) or [0])
            .execute()
        ).data or []
        solution_ids = {r.get("solution_id") for r in solution_needs}
        solutions = [r for r in _rows("solutions", company_id) if r.get("id") in solution_ids]

        solution_actions = (
            database.table("solution_actions")
            .select("*")
            .in_("solution_id", list(solution_ids) or [0])
            .order("sequence_order")
            .execute()
        ).data or []
        action_ids = {r.get("action_id") for r in solution_actions}
        actions = [r for r in _rows("actions", company_id) if r.get("id") in action_ids]

        # Determine the first incomplete semantic stage. This is guidance only;
        # execution remains the responsibility of the decision/workflow layer.
        next_step = None
        if requirements:
            next_step = {
                "type": "collect_requirements",
                "requirements": requirements,
            }
        elif needs:
            next_step = {
                "type": "clarify_need",
                "needs": needs,
            }
        elif solutions:
            next_step = {
                "type": "present_solution",
                "solutions": solutions,
            }
        elif actions:
            next_step = {
                "type": "prepare_action",
                "actions": actions,
            }

        return {
            "intent": intent,
            "needs": needs,
            "requirements": requirements,
            "solutions": solutions,
            "actions": actions,
            "next_step": next_step,
            "reasoning_found": bool(needs or requirements or solutions or actions),
        }
    except Exception as error:
        print("[BUSINESS REASONING ERROR]", error)
        return empty
