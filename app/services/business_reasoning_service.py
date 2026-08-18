"""
Bitey Business Reasoning Layer V1

Resolves the semantic business chain:
Intent -> Need -> Requirements -> Solution -> Actions

This layer is intentionally read-only. It does not execute actions or
workflows and does not apply commercial subscription limits.
"""

from typing import Any, Dict, List, Optional

from app.database.supabase import database


def _rows(table: str, company_id: int) -> List[Dict[str, Any]]:
    response = (
        database.table(table)
        .select("*")
        .eq("company_id", company_id)
        .execute()
    )
    return response.data or []


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
        intents = (
            database.table("intents")
            .select("*")
            .eq("company_id", company_id)
            .eq("code", intent_code)
            .eq("is_active", True)
            .limit(1)
            .execute()
        ).data or []

        if not intents:
            return empty

        intent = intents[0]
        needs = [
            row for row in _rows("needs", company_id)
            if row.get("intent_id") == intent.get("id") and row.get("is_active", True)
        ]

        requirements = []
        for requirement in _rows("requirements", company_id):
            if any(requirement.get("need_id") == need.get("id") for need in needs):
                requirements.append(requirement)

        solutions = _rows("solutions", company_id)
        solution_needs = (
            database.table("solution_needs")
            .select("*")
            .execute()
        ).data or []
        solution_ids = {
            row.get("solution_id")
            for row in solution_needs
            if row.get("need_id") in {need.get("id") for need in needs}
        }
        solutions = [
            solution for solution in solutions
            if solution.get("id") in solution_ids and solution.get("is_active", True)
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
            action for action in _rows("actions", company_id)
            if action.get("id") in action_ids and action.get("is_active", True)
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
