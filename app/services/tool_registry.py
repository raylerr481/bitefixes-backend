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

    result = (
        database.table("tools")
        .select("*")
        .eq("code", tool_code)
        .eq("is_active", True)
        .execute()
    )
    tools = result.data or []

    if company_id is not None:
        for tool in tools:
            if tool.get("company_id") == company_id:
                return _with_connector_id(tool)

    for tool in tools:
        if tool.get("company_id") is None:
            return _with_connector_id(tool)

    return None


def _with_connector_id(tool: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve connector ownership from configuration or connector catalog."""
    if tool.get("connector_id"):
        return tool

    config = tool.get("configuration") or {}
    connector_code = config.get("connector_code") if isinstance(config, dict) else None
    if not connector_code:
        connector_code = "rest_api" if tool.get("code", "").startswith("rest_api_") else None

    if not connector_code:
        return tool

    catalog = (
        database.table("connector_catalog")
        .select("id, code")
        .eq("code", connector_code)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    if catalog.data:
        tool = dict(tool)
        tool["connector_id"] = catalog.data[0]["id"]
    return tool


def tool_supports_action(tool: Dict[str, Any], action_code: str) -> bool:
    """Check whether a registered tool declares an action/capability."""
    capabilities = tool.get("capabilities") or []
    if isinstance(capabilities, dict):
        capabilities = list(capabilities.keys())
    return action_code in capabilities
