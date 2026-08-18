"""Bitey permission and policy engine.

This module evaluates whether a tool action may execute. It does not perform
external calls. Execution must happen in a connector runtime after this check.
"""

from typing import Any, Dict, Optional

from app.database.supabase import database
from app.services.tool_registry import get_tool, tool_supports_action


class PermissionDecision:
    def __init__(
        self,
        allowed: bool,
        requires_approval: bool = False,
        reason: str = "",
        tool: Optional[Dict[str, Any]] = None,
        permission: Optional[Dict[str, Any]] = None,
    ):
        self.allowed = allowed
        self.requires_approval = requires_approval
        self.reason = reason
        self.tool = tool
        self.permission = permission

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "requires_approval": self.requires_approval,
            "reason": self.reason,
            "tool_code": self.tool.get("code") if self.tool else None,
            "action_code": self.permission.get("action_code") if self.permission else None,
        }


def evaluate_permission(
    company_id: int,
    tool_code: str,
    action_code: str,
    connection_id: Optional[int] = None,
) -> PermissionDecision:
    """Evaluate connection, tool and company permission policy.

    Default deny is intentional. A missing connection, tool capability, or
    permission never results in an external execution.
    """
    if not company_id:
        return PermissionDecision(False, reason="company_required")
    if not tool_code or not action_code:
        return PermissionDecision(False, reason="tool_and_action_required")

    tool = get_tool(tool_code, company_id)
    if not tool:
        return PermissionDecision(False, reason="tool_not_found")

    if not tool_supports_action(tool, action_code):
        return PermissionDecision(False, reason="action_not_declared", tool=tool)

    connection_query = (
        database.table("company_connections")
        .select("*")
        .eq("company_id", company_id)
        .eq("is_active", True)
    )
    if connection_id is not None:
        connection_query = connection_query.eq("id", connection_id)
    else:
        connection_query = connection_query.eq("connector_id", tool.get("connector_id", -1))

    connection_result = connection_query.execute()
    connections = connection_result.data or []
    if not connections:
        return PermissionDecision(False, reason="active_connection_not_found", tool=tool)

    resolved_connection = connections[0]
    resolved_connection_id = resolved_connection.get("id")

    permission_query = (
        database.table("tool_permissions")
        .select("*")
        .eq("company_id", company_id)
        .eq("tool_code", tool_code)
        .eq("action_code", action_code)
        .eq("is_active", True)
    )
    permission_result = permission_query.execute()
    permissions = permission_result.data or []

    permission = None
    for candidate in permissions:
        candidate_connection = candidate.get("connection_id")
        if candidate_connection in (None, resolved_connection_id):
            permission = candidate
            if candidate_connection == resolved_connection_id:
                break

    if not permission:
        return PermissionDecision(False, reason="permission_denied", tool=tool)

    if permission.get("permission") != "allow":
        return PermissionDecision(False, reason="permission_denied", tool=tool, permission=permission)

    if permission.get("approval_required"):
        return PermissionDecision(
            False,
            requires_approval=True,
            reason="approval_required",
            tool=tool,
            permission=permission,
        )

    return PermissionDecision(True, reason="permission_granted", tool=tool, permission=permission)
