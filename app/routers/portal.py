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


def _signal_evidence(signal: dict) -> str | None:
    evidence = signal.get("evidence")
    if not evidence:
        return None
    # Existing rows can contain mojibake from an earlier encoding boundary.
    # Decode only when the round-trip is clearly reversible; never invent text.
    if "Ã" in evidence or "â" in evidence:
        try:
            repaired = evidence.encode("latin-1").decode("utf-8")
            if repaired:
                return repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return evidence


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
    return {"status": "success", "customers": _rows(
        "customers", filters={"company_id": company_id, "is_active": True},
        order="updated_at:true", limit=limit,
    )}


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
    return {"status": "success", "tickets": _rows(
        "tickets", filters=filters, order="updated_at:true", limit=limit,
    )}


@router.get("/tickets/{ticket_id}")
def portal_ticket(ticket_id: int):
    ticket = _one("tickets", ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    messages = _rows("messages", filters={"ticket_id": ticket_id}, order="created_at:false", limit=100)
    return {"status": "success", "ticket": ticket, "messages": messages}


@router.get("/conversations")
def portal_conversations(company_id: int = Query(1), customer_id: int | None = None,
                         limit: int = Query(50, ge=1, le=200)):
    filters = {}
    if customer_id is not None:
        filters["customer_id"] = customer_id
    rows = _rows("conversations", filters=filters, order="updated_at:true", limit=limit)
    return {"status": "success", "company_id": company_id, "conversations": rows}


@router.get("/conversations/{conversation_id}")
def portal_conversation(conversation_id: int):
    conversation = _one("conversations", conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = _rows("messages", filters={"conversation_id": conversation_id}, order="created_at:false", limit=100)
    return {"status": "success", "conversation": conversation, "messages": messages}


@router.get("/cognitive/{conversation_id}")
def portal_cognitive(conversation_id: int):
    conversation = _one("conversations", conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    problems = _rows("bitey_problems", filters={"conversation_id": conversation_id}, order="updated_at:true", limit=20)
    commitments = _rows("conversation_commitments", filters={"conversation_id": conversation_id}, order="updated_at:true", limit=20)
    signals = _rows("contextual_signals", filters={"conversation_id": str(conversation_id)}, order="created_at:true", limit=50)

    active_problem = next((p for p in problems if p.get("state") not in {"resolved", "closed"}), None)
    active_commitment = next((c for c in commitments if c.get("state") not in {"resolved", "closed"}), None)

    known_facts = []
    if active_problem:
        for key, label in (("device_label", "device"), ("device_platform", "platform"), ("symptoms", None), ("evidence", None)):
            value = active_problem.get(key)
            if value:
                known_facts.append(f"{label}: {value}" if label else value)

    # If no formal problem/commitment exists yet, derive only observable facts
    # from detected signals. This is a projection, not a new inference.
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

    # Do not invent objective/problem/action. Only expose values persisted in
    # the canonical cognitive records or directly observable signals.
    active_objective = active_commitment.get("objective") if active_commitment else None
    current_problem = active_problem.get("problem_summary") if active_problem else None
    evidence = active_problem.get("evidence") if active_problem else [
        _signal_evidence(s) for s in signals if _signal_evidence(s)
    ]
    evidence = list(dict.fromkeys(evidence))
    contradictions = [s for s in signals if str(s.get("signal_type", "")).lower() in {"contradiction", "conflict"}]
    confidence = (active_problem or active_commitment or {}).get("confidence")

    return {
        "status": "success",
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
