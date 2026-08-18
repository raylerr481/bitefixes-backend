"""Bitey connector runtime.

Executes only after the permission engine has explicitly authorized an action.
The initial runtime is intentionally read-only and supports HTTP GET calls.
"""

from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

from app.services.permission_engine import evaluate_permission


class ConnectorExecutionError(RuntimeError):
    """Raised when a connector operation cannot be safely executed."""


def execute_rest_read(
    company_id: int,
    tool_code: str,
    connection: Dict[str, Any],
    path: str = "",
    query: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 15,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Execute a REST GET only after policy authorization.

    dry_run=True returns the planned request without making a network call.
    Credentials must be resolved by the deployment's secret manager; this
    runtime never accepts raw secrets from an AI-generated request.
    """
    connection_id = connection.get("id")
    decision = evaluate_permission(
        company_id=company_id,
        tool_code=tool_code,
        action_code="read",
        connection_id=connection_id,
    )
    if not decision.allowed:
        return {
            "executed": False,
            "dry_run": dry_run,
            "requires_approval": decision.requires_approval,
            "reason": decision.reason,
        }

    base_url = connection.get("endpoint_url")
    if not base_url:
        raise ConnectorExecutionError("connection_endpoint_missing")

    url = urljoin(base_url.rstrip("/") + "/", str(path).lstrip("/"))
    request_headers = {"Accept": "application/json"}
    if headers:
        # Only non-sensitive request headers may be supplied by the caller.
        request_headers.update(headers)

    plan = {
        "method": "GET",
        "url": url,
        "query": query or {},
        "headers": {k: v for k, v in request_headers.items() if k.lower() != "authorization"},
    }

    if dry_run:
        return {"executed": False, "dry_run": True, "reason": "dry_run", "request": plan}

    response = requests.get(url, params=query or {}, headers=request_headers, timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        data: Any = response.json()
    else:
        data = response.text

    return {
        "executed": True,
        "dry_run": False,
        "status_code": response.status_code,
        "data": data,
    }
