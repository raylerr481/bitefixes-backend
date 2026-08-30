"""Support Portal read API.

The browser talks to BiteFixes Backend; privileged Supabase credentials never
leave the server. This router exposes a compact, read-only projection for the
WordPress Support Portal and the Bitey cognitive state panel.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.database.supabase import supabase_manager

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


def _one(table: str, record_id: int, select: str = "*"):
    rows = _rows(table, select=select, filters={"id": record_id}, limit=1)
    return rows[0] if rows else None


@router.get("/status")
def portal_status():
    return {
        "status": "ready",
        "portal": "bitefixes-support",
        "gateway": "bitey-cloud",
        "canonical_database": "supabase",
        "supabase_connected": bool(supabase_manager.check_connection()),
        "cognitive_projection": "enabled",
    }


@router.get("/customers")
def portal_customers(company_id: int = Query(1), limit: int = Query(50, ge=1, le=200)):
    return {
        "status": "success",
        "customers": _rows(
            "customers",
            filters={"company_id": company_id, "is_active": True},
            order="updated_at:true",
            limit=limit,
        ),
    }


@router.get("/customers/{customer_id}")
def portal_customer(customer_id: int):
    customer = _one("customers", customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"status": "success", "customer": customer}


@router.get("/tickets")
def portal_tickets(company_id: int = Query(1), status: str | None = None,
                  limit: int = Query(50, ge=1, le=200)):
    filters = {"company_id": company_id}
    if status:
        filters["status"] = status
    return {
        "status": "success",
        "tickets": _rows("tickets", filters=filters, order="updated_at:true", limit=limit),
    }


@router.get("/tickets/{ticket_id}")
def portal_ticket(ticket_id: int):
    ticket = _one("tickets", ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    messages = _rows(
        "messages",
        filters={"ticket_id": ticket_id},
        order="created_at:false",
        limit=100,
    )
    return {"status": "success", "ticket": ticket, "messages": messages}


@router.get("/conversations")
def portal_conversations(company_id: int = Query(1), customer_id: int | None = None,
                         limit: int = Query(50, ge=1, le=200)):
    filters = {}
    if customer_id is not None:
        filters["customer_id"] = customer_id
    rows = _rows("conversations", filters=filters, order="updated_at:true", limit=limit)
    # conversations has no company_id in the canonical schema; customer/ticket
    # ownership is resolved through the linked records by the portal consumer.
    return {"status": "success", "company_id": company_id, "conversations": rows}


@router.get("/conversations/{conversation_id}")
def portal_conversation(conversation_id: int):
    conversation = _one("conversations", conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = _rows(
        "messages",
        filters={"conversation_id": conversation_id},
        order="created_at:false",
        limit=100,
    )
    return {"status": "success", "conversation": conversation, "messages": messages}


@router.get("/cognitive/{conversation_id}")
def portal_cognitive(conversation_id: int):
    conversation = _one("conversations", conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    problems = _rows(
        "bitey_problems",
        filters={"conversation_id": conversation_id},
        order="updated_at:true",
        limit=20,
    )
    commitments = _rows(
        "conversation_commitments",
        filters={"conversation_id": conversation_id},
        order="updated_at:true",
        limit=20,
    )
    signals = _rows(
        "contextual_signals",
        filters={"conversation_id": str(conversation_id)},
        order="created_at:true",
        limit=50,
    )

    active_problem = next((p for p in problems if p.get("state") not in {"resolved", "closed"}), None)
    active_commitment = next((c for c in commitments if c.get("state") not in {"resolved", "closed"}), None)

    known_facts = []
    if active_problem:
        if active_problem.get("device_label"):
            known_facts.append(f"device: {active_problem['device_label']}")
        if active_problem.get("device_platform"):
            known_facts.append(f"platform: {active_problem['device_platform']}")
        if active_problem.get("symptoms"):
            known_facts.append(active_problem["symptoms"])
        if active_problem.get("evidence"):
            known_facts.append(active_problem["evidence"])

    missing = active_commitment.get("missing_requirements", []) if active_commitment else []
    next_action = active_commitment.get("next_action") if active_commitment else None

    return {
        "status": "success",
        "conversation_id": conversation_id,
        "customer_id": conversation.get("customer_id"),
        "ticket_id": conversation.get("ticket_id"),
        "active_objective": active_commitment.get("state") if active_commitment else None,
        "current_problem": active_problem.get("problem_summary") if active_problem else None,
        "known_facts": known_facts,
        "missing_information": missing,
        "evidence": active_problem.get("evidence") if active_problem else [],
        "contradictions": [s for s in signals if s.get("signal_type") in {"contradiction", "conflict"}],
        "next_action": next_action,
        "confidence": (active_problem or active_commitment or {}).get("confidence"),
        "problems": problems,
        "commitments": commitments,
        "signals": signals,
    }
