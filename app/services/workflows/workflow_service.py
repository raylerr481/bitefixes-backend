"""
Bitey Workflow Router V22
=========================

Central workflow executor with a Supabase-first configuration model and
legacy Python fallback.

Resolution order:
    1. Company-specific active workflow in Supabase
    2. Global active workflow in Supabase
    3. Legacy WORKFLOW_MAP

The fallback keeps existing Bitey workflows operational while the new
workflow catalog is populated incrementally.
"""

import importlib
from typing import Any, Dict, Optional

from app.database.supabase import database


WORKFLOW_MAP = {
    "cctv_installation": "app.services.workflows.camera_installation",
    "windows_installation": "app.services.workflows.windows_installation",
    "hardware_upgrade": "app.services.workflows.hardware_upgrade",
    "computer_repair": "app.services.workflows.computer_repair",
    "network_configuration": "app.services.workflows.network_support",
}


def _workflow_rows(intent: str, company_id: Optional[int] = None):
    """Load active workflow definitions without making Supabase mandatory."""
    query = (
        database.table("workflows")
        .select("*")
        .eq("intent", intent)
        .eq("is_active", True)
    )

    if company_id is not None:
        query = query.or_(f"company_id.eq.{company_id},company_id.is.null")
    else:
        query = query.is_("company_id", "null")

    response = query.execute()
    return response.data or []


def _select_workflow(rows, company_id: Optional[int] = None):
    """Prefer company-specific configuration over global configuration."""
    if company_id is not None:
        company_rows = [
            row for row in rows if row.get("company_id") == company_id
        ]
        if company_rows:
            return company_rows[0]

    global_rows = [row for row in rows if row.get("company_id") is None]
    return global_rows[0] if global_rows else None


def _resolve_workflow(intent: str, company_id: Optional[int] = None) -> Dict[str, Any]:
    """Resolve the configured workflow and retain legacy compatibility."""
    try:
        configured = _select_workflow(_workflow_rows(intent, company_id), company_id)
    except Exception as exc:
        # Database configuration must not take down the legacy workflow path.
        print("[WORKFLOW CONFIG WARNING]", repr(exc))
        configured = None

    if configured:
        definition = configured.get("definition") or {}
        module_path = (
            configured.get("module_path")
            or definition.get("module_path")
            or WORKFLOW_MAP.get(intent)
        )
        return {
            "configured": True,
            "workflow": configured,
            "module_path": module_path,
        }

    return {
        "configured": False,
        "workflow": None,
        "module_path": WORKFLOW_MAP.get(intent),
    }


def execute_workflow(
    intent,
    message,
    company_id=None,
    customer_id=None,
    service_id=None,
    customer=None,
    language=None,
    knowledge=None,
    business_context=None,
    **kwargs,
):
    """Execute a workflow resolved from business configuration or legacy map."""

    resolution = _resolve_workflow(intent, company_id)
    module_path = resolution["module_path"]
    configured = resolution["workflow"]

    if not module_path:
        return {
            "success": False,
            "workflow": None,
            "response": "No workflow configured.",
        }

    try:
        module = importlib.import_module(module_path)

        result = module.execute(
            message=message,
            company_id=company_id,
            customer_id=customer_id,
            service_id=service_id,
            intent=intent,
            customer=customer,
            language=language,
        )

        if isinstance(result, dict):
            result.setdefault("workflow_configured", bool(configured))
            if configured:
                result.setdefault("workflow_id", configured.get("id"))

        return result

    except Exception as e:
        print("[WORKFLOW EXECUTION ERROR]", repr(e))

        return {
            "success": False,
            "workflow": intent,
            "response": "Workflow execution failed.",
            "error": str(e),
        }
