"""Operational incident capture and governed self-repair primitives for Bitey."""
from __future__ import annotations

import hashlib
import os
from typing import Any

from app.database.supabase import supabase_manager


ALERT_RECIPIENT = os.getenv("BITEY_ALERT_EMAIL", "raylerr481@gmail.com")


def fingerprint(*parts: str | None) -> str:
    raw = "|".join((p or "").strip().lower() for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def record_incident(
    *,
    message: str,
    severity: str = "error",
    component: str | None = None,
    error_code: str | None = None,
    error_type: str | None = None,
    route: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    operation: str | None = None,
    company_id: int | None = None,
    context: dict[str, Any] | None = None,
    stack_trace: str | None = None,
) -> dict[str, Any]:
    """Upsert an incident and enqueue an alert without exposing secrets."""
    fp = fingerprint(component, error_code, error_type, route, provider, operation, message)
    payload = {
        "company_id": company_id,
        "environment": os.getenv("APP_ENV", "production"),
        "service": os.getenv("PROJECT_NAME", "bitefixes-backend"),
        "component": component,
        "severity": severity,
        "status": "open",
        "error_code": error_code,
        "error_type": error_type,
        "message": message[:4000],
        "fingerprint": fp,
        "route": route,
        "provider": provider,
        "model": model,
        "operation": operation,
        "context": context or {},
        "stack_trace": stack_trace,
    }
    client = supabase_manager.client
    existing = client.table("bitey_incidents").select("id,occurrence_count").eq("fingerprint", fp).eq("status", "open").limit(1).execute()
    if existing.data:
        incident_id = existing.data[0]["id"]
        count = int(existing.data[0].get("occurrence_count", 1)) + 1
        client.table("bitey_incidents").update({"occurrence_count": count, "last_seen_at": "now()", "updated_at": "now()", "context": context or {}}).eq("id", incident_id).execute()
        return {"incident_id": incident_id, "deduplicated": True, "fingerprint": fp}

    inserted = client.table("bitey_incidents").insert(payload).execute()
    incident_id = inserted.data[0]["id"] if inserted.data else None
    if incident_id:
        client.table("bitey_alert_outbox").insert({
            "incident_id": incident_id,
            "company_id": company_id,
            "recipient": ALERT_RECIPIENT,
            "channel": "email",
            "subject": f"[Bitey {severity.upper()}] {component or 'backend'}: {error_code or error_type or 'incident'}",
            "body": f"Bitey detected an incident. ID={incident_id}; component={component}; provider={provider}; operation={operation}; message={message[:2000]}",
            "priority": "critical" if severity == "critical" else ("high" if severity == "error" else "normal"),
        }).execute()
    return {"incident_id": incident_id, "deduplicated": False, "fingerprint": fp}


def plan_safe_remediation(incident_id: int, action_type: str, result: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create an auditable remediation plan. High-risk actions require approval."""
    risk = "low" if action_type in {"retry_provider", "switch_provider", "invalidate_cache", "rebuild_vector_index"} else "medium"
    requires_approval = risk != "low"
    client = supabase_manager.client
    row = client.table("bitey_remediation_runs").insert({
        "incident_id": incident_id,
        "action_type": action_type,
        "action_status": "planned",
        "risk_level": risk,
        "requires_approval": requires_approval,
        "result": result or {},
    }).execute()
    return row.data[0] if row.data else {"incident_id": incident_id, "action_type": action_type, "action_status": "planned"}
