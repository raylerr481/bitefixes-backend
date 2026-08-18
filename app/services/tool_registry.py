"""Bitey Tool Registry.

Resolves active tools and their declared capabilities without executing them.
The registry is deliberately separate from connector runtime and permission
checking so the AI layer cannot call an external system directly.
"""

from typing import Any, Dict, Optional

from app.database.supabase import database


def get_tool(tool_code: str, company_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Return an active tool, preferring a company-specific tool over global."""
    if not tool_code:
        return None

    query = (
        database.table("tools")
        .select("*")
        .eq("code", tool_code)
        .eq("is_active", True)
    )

    result = query.execute()
    tools = result.data or []

    if company_id is not None:
        for tool in tools:
            if tool.get("company_id") == company_id:
                return tool

    for tool in tools:
        if tool.get("company_id") is None:
            return tool

    return None


def tool_supports_action(tool: Dict[str, Any], action_code: str) -> bool:
    """Check whether a registered tool declares an action/capability."""
    capabilities = tool.get("capabilities") or []
    if isinstance(capabilities, dict):
        capabilities = list(capabilities.keys())
    return action_code in capabilities
