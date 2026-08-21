"""Bitey Workflow Router V24.

Supabase-first workflow resolution with a broad legacy fallback catalog.
"""

import importlib
from typing import Any, Dict, Optional

from app.database.supabase import database


WORKFLOW_MAP = {
    "cctv_installation": "app.services.workflows.camera_installation",
    "camera_installation": "app.services.workflows.camera_installation",
    "windows_installation": "app.services.workflows.windows_installation",
    "hardware_upgrade": "app.services.workflows.hardware_upgrade",
    "computer_repair": "app.services.workflows.computer_repair",
    "network_configuration": "app.services.workflows.network_support",
    "mobile_repair": "app.services.workflows.mobile_repair",
}


def _workflow_rows(intent: str, company_id: Optional[int] = None):
    query = database.table("workflows").select("*").eq("intent", intent).eq("is_active", True)
    if company_id is not None:
        query = query.or_(f"company_id.eq.{company_id},company_id.is.null")
    else:
        query = query.is_("company_id", "null")
    response = query.execute()
    return response.data or []


def _select_workflow(rows, company_id: Optional[int] = None):
    if company_id is not None:
        company_rows = [row for row in rows if row.get("company_id") == company_id]
        if company_rows:
            return company_rows[0]
    global_rows = [row for row in rows if row.get("company_id") is None]
    return global_rows[0] if global_rows else None


def _resolve_workflow(intent: str, company_id: Optional[int] = None) -> Dict[str, Any]:
    try:
        configured = _select_workflow(_workflow_rows(intent, company_id), company_id)
    except Exception as exc:
        print("[WORKFLOW CONFIG WARNING]", repr(exc))
        configured = None

    if configured:
        definition = configured.get("definition") or {}
        module_path = configured.get("module_path") or definition.get("module_path") or WORKFLOW_MAP.get(intent)
        return {"configured": True, "workflow": configured, "module_path": module_path}

    return {"configured": False, "workflow": None, "module_path": WORKFLOW_MAP.get(intent)}


def execute_workflow(intent, message, company_id=None, customer_id=None, service_id=None, customer=None, language=None, knowledge=None, business_context=None, **kwargs):
    """Execute a company workflow or a safe built-in fallback."""
    resolution = _resolve_workflow(intent, company_id)
    module_path = resolution["module_path"]
    configured = resolution["workflow"]

    if not module_path:
        return {"success": False, "workflow": None, "response": "Aún necesito configurar el flujo para esa solicitud.", "reason": "workflow_not_configured"}

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
            knowledge=knowledge,
            business_context=business_context,
            **kwargs,
        )
        if isinstance(result, dict):
            result.setdefault("workflow_configured", bool(configured))
            if configured:
                result.setdefault("workflow_id", configured.get("id"))
        return result
    except Exception as error:
        print("[WORKFLOW EXECUTION ERROR]", repr(error))
        return {"success": False, "workflow": intent, "response": "No pude completar ese flujo todavía. Puedo continuar con el diagnóstico contigo.", "reason": "workflow_execution_failed", "error": str(error)}
