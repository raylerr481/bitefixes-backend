"""Protected Support Portal API."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.database.supabase import supabase_manager
from app.routers.portal_auth import require_portal_admin, require_portal_user
from app.services.ticket_service import process_ticket, update_ticket

router = APIRouter(prefix="/portal", tags=["Support Portal"])


def _rows(table: str, *, select: str = "*", filters: dict | None = None,
          order: str | None = None, limit: int | None = None):
    query = supabase_manager.table(table).select(select)
    for column, value in (filters or {}).items():
        query = query.eq(column, value)
    if order:
        column, descending = order.split(":", 1) if ":" in order else (order, "false")
        query = query.order(column, desc=descending.lower() == "true")
    if limit:
        query = query.limit(limit)
    response = query.execute()
    return response.data or []


def _one_for_company(table: str, record_id: int, company_id: int, select: str = "*"):
    rows = _rows(table, select=select, filters={"id": record_id, "company_id": company_id}, limit=1)
    return rows[0] if rows else None


def _customer_ids(company_id: int) -> set[int]:
    rows = _rows("customers", select="id", filters={"company_id": company_id, "is_active": True}, limit=10000)
    return {int(row["id"]) for row in rows if row.get("id") is not None}


def _signal_evidence(signal: dict) -> str | None:
    evidence = signal.get("evidence")
    if not evidence:
        return None
    if "Ã" in evidence or "â" in evidence:
        try:
            repaired = evidence.encode("latin-1").decode("utf-8")
            if repaired:
                return repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return evidence


@router.get("/status")
def portal_status(context=Depends(require_portal_user)):
    return {
        "status": "ready",
        "portal": "bitefixes-support",
        "gateway": "bitey-cloud",
        "canonical_database": "supabase",
        "supabase_connected": bool(supabase_manager.check_connection()),
        "cognitive_projection": "enabled",
        "company_id": context["company_id"],
        "role": context["role"],
    }


@router.get("/customers")
def portal_customers(
    company_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    context=Depends(require_portal_user),
):
    effective_company_id = context["company_id"]
    if company_id is not None and company_id != effective_company_id:
        raise HTTPException(status_code=403, detail="Cross-company access is not allowed")
    return {"status": "success", "company_id": effective_company_id, "customers": _rows(
        "customers", filters={"company_id": effective_company_id, "is_active": True},
        order="updated_at:true", limit=limit,
    )}


@router.get("/customers/{customer_id}")
def portal_customer(customer_id: int, context=Depends(require_portal_user)):
    customer = _one_for_company("customers", customer_id, context["company_id"])
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"status": "success", "company_id": context["company_id"], "customer": customer}


@router.get("/tickets")
def portal_tickets(
    company_id: int | None = Query(None),
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    context=Depends(require_portal_user),
):
    effective_company_id = context["company_id"]
    if company_id is not None and company_id != effective_company_id:
        raise HTTPException(status_code=403, detail="Cross-company access is not allowed")
    filters = {"company_id": effective_company_id}
    if status:
        filters["status"] = status
    return {"status": "success", "company_id": effective_company_id, "tickets": _rows(
        "tickets", filters=filters, order="updated_at:true", limit=limit,
    )}


@router.get("/tickets/{ticket_id}")
def portal_ticket(ticket_id: int, context=Depends(require_portal_user)):
    ticket = _one_for_company("tickets", ticket_id, context["company_id"])
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    messages = _rows(
        "messages",
        filters={"ticket_id": ticket_id, "company_id": context["company_id"]},
        order="created_at:false",
        limit=100,
    )
    return {"status": "success", "company_id": context["company_id"], "ticket": ticket, "messages": messages}


@router.post("/tickets", status_code=201)
def portal_create_ticket(
    payload: dict[str, Any] = Body(...),
    context=Depends(require_portal_user),
):
    """Create a ticket from the protected portal tenant context.

    company_id is deliberately taken from the authenticated context rather
    than from the client payload. Related records are checked against the
    same company before the shared ticket service is called.
    """
    company_id = context["company_id"]

    customer_id = payload.get("customer_id")
    if customer_id is None:
        raise HTTPException(status_code=422, detail="customer_id is required")
    try:
        customer_id = int(customer_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="customer_id must be an integer")

    customer = _one_for_company("customers", customer_id, company_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found for this company")

    service_id = payload.get("service_id")
    if service_id is not None:
        try:
            service_id = int(service_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="service_id must be an integer")
        if not _one_for_company("services", service_id, company_id):
            raise HTTPException(status_code=404, detail="Service not found for this company")

    device_id = payload.get("device_id")
    if device_id is not None:
        try:
            device_id = int(device_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="device_id must be an integer")
        device = _one_for_company("customer_devices", device_id, company_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found for this company")
        if device.get("customer_id") not in {customer_id, str(customer_id)}:
            raise HTTPException(status_code=409, detail="Device does not belong to the selected customer")

    technician_id = payload.get("technician_id")
    if technician_id is not None:
        try:
            technician_id = int(technician_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="technician_id must be an integer")
        technician = _one_for_company("company_people", technician_id)
        if not technician or not technician.get("is_active", True):
            raise HTTPException(status_code=404, detail="Technician not found for this company")

    description = str(payload.get("description") or "").strip()
    if not description:
        raise HTTPException(status_code=422, detail="description is required")

    ticket = process_ticket(
        company_id=company_id,
        customer_id=customer_id,
        service_id=service_id,
        intent=payload.get("intent"),
        description=description,
        title=str(payload.get("title") or "Solicitud de soporte").strip(),
        language=str(payload.get("language") or "es"),
        channel=str(payload.get("channel") or "portal"),
        ticket_type=str(payload.get("ticket_type") or "technical_support"),
    )
    if not ticket:
        raise HTTPException(status_code=500, detail="Unable to create or retrieve ticket")

    ticket_id = ticket.get("id")
    extra = {}
    if technician_id is not None:
        extra["technician_id"] = technician_id
    if device_id is not None:
        extra["device_id"] = device_id
    if payload.get("priority"):
        extra["priority"] = payload["priority"]
    if payload.get("notes"):
        extra["notes"] = payload["notes"]
    if extra and ticket_id is not None:
        updated = update_ticket(ticket_id, extra)
        if updated:
            ticket = updated

    return {
        "status": "success",
        "company_id": company_id,
        "ticket": ticket,
        "created_by": context.get("user_id"),
        "cognitive_projection": "enabled",
    }


@router.get("/conversations")
def portal_conversations(
    company_id: int | None = Query(None),
    customer_id: int | None = None,
    limit: int = Query(50, ge=1, le=200),
    context=Depends(require_portal_user),
):
    effective_company_id = context["company_id"]
    if company_id is not None and company_id != effective_company_id:
        raise HTTPException(status_code=403, detail="Cross-company access is not allowed")
    customer_ids = _customer_ids(effective_company_id)
    if customer_id is not None:
        if customer_id not in customer_ids:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer_ids = {customer_id}
    if not customer_ids:
        return {"status": "success", "company_id": effective_company_id, "conversations": []}
    rows = _rows("conversations", order="updated_at:true", limit=min(max(limit * 3, limit), 500))
    rows = [row for row in rows if row.get("customer_id") in customer_ids][:limit]
    return {"status": "success", "company_id": effective_company_id, "conversations": rows}


@router.get("/conversations/{conversation_id}")
def portal_conversation(conversation_id: int, context=Depends(require_portal_user)):
    company_id = context["company_id"]
    conversation = next(
        (row for row in _rows("conversations", filters={"id": conversation_id}, limit=1)
         if row.get("customer_id") in _customer_ids(company_id)),
        None,
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = _rows(
        "messages",
        filters={"conversation_id": conversation_id, "company_id": company_id},
        order="created_at:false",
        limit=100,
    )
    return {"status": "success", "company_id": company_id, "conversation": conversation, "messages": messages}


@router.get("/cognitive/{conversation_id}")
def portal_cognitive(conversation_id: int, context=Depends(require_portal_user)):
    company_id = context["company_id"]
    conversation = next(
        (row for row in _rows("conversations", filters={"id": conversation_id}, limit=1)
         if row.get("customer_id") in _customer_ids(company_id)),
        None,
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    problems = _rows("bitey_problems", filters={"conversation_id": conversation_id, "company_id": company_id}, order="updated_at:true", limit=20)
    commitments = _rows("conversation_commitments", filters={"conversation_id": conversation_id, "company_id": company_id}, order="updated_at:true", limit=20)
    signals = _rows("contextual_signals", filters={"conversation_id": str(conversation_id), "company_id": str(company_id)}, order="created_at:true", limit=50)

    active_problem = next((p for p in problems if p.get("state") not in {"resolved", "closed"}), None)
    active_commitment = next((c for c in commitments if c.get("state") not in {"resolved", "closed"}), None)

    known_facts = []
    if active_problem:
        for key, label in (("device_label", "device"), ("device_platform", "platform"), ("symptoms", None), ("evidence", None)):
            value = active_problem.get(key)
            if value:
                known_facts.append(f"{label}: {value}" if label else value)

    if not known_facts:
        for signal in reversed(signals):
            value = signal.get("signal_value")
            evidence = _signal_evidence(signal)
            if value and signal.get("signal_type") in {"SERVICE_REQUEST", "NEED", "CONTACT_REQUEST", "CONVERSATION_CONTINUITY"}:
                known_facts.append(f"{signal.get('signal_type')}: {value}")
            if evidence and evidence not in known_facts:
                known_facts.append(evidence)

    missing = active_commitment.get("missing_requirements", []) if active_commitment else []
    next_action = active_commitment.get("next_action") if active_commitment else None
    active_objective = active_commitment.get("objective") if active_commitment else None
    current_problem = active_problem.get("problem_summary") if active_problem else None
    evidence = active_problem.get("evidence") if active_problem else [_signal_evidence(s) for s in signals if _signal_evidence(s)]
    evidence = list(dict.fromkeys(evidence))
    contradictions = [s for s in signals if str(s.get("signal_type", "")).lower() in {"contradiction", "conflict"}]
    confidence = (active_problem or active_commitment or {}).get("confidence")

    return {
        "status": "success",
        "company_id": company_id,
        "conversation_id": conversation_id,
        "customer_id": conversation.get("customer_id"),
        "ticket_id": conversation.get("ticket_id"),
        "active_objective": active_objective,
        "current_problem": current_problem,
        "known_facts": list(dict.fromkeys(known_facts)),
        "missing_information": missing,
        "evidence": evidence,
        "contradictions": contradictions,
        "next_action": next_action,
        "confidence": confidence,
        "problems": problems,
        "commitments": commitments,
        "signals": signals,
    }


@router.get("/employees")
def portal_employees(context=Depends(require_portal_admin)):
    company_id = context["company_id"]
    people = _rows("company_people", filters={"company_id": company_id, "is_active": True}, order="full_name:false", limit=200)
    for person in people:
        person["roles"] = _rows("company_person_roles", filters={"company_person_id": person["id"], "is_active": True}, order="authority_level:true", limit=20)
    return {"status": "success", "company_id": company_id, "employees": people}
