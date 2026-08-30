"""Idempotent SupportCandy -> BiteFixes/Supabase synchronization."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.database.supabase import database
from app.integrations.supportcandy.client import SupportCandyClient
from app.services.customer_service import get_or_create_customer
from app.services.ticket_service import create_ticket

COMPANY_ID = 1
CHANNEL = "portal"


def _text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("label") or value.get("slug") or value.get("id") or "").strip()
    return str(value or "").strip()


def _status(value: Any) -> str:
    raw = _text(value).lower()
    return {"open": "open", "new": "open", "in-progress": "in_progress", "in progress": "in_progress", "pending": "pending", "closed": "closed", "resolved": "closed"}.get(raw, "open")


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _registry(entity_type: str, external_id: str) -> dict[str, Any] | None:
    result = (database.table("supportcandy_sync_registry").select("*")
              .eq("company_id", COMPANY_ID).eq("entity_type", entity_type)
              .eq("external_id", external_id).limit(1).execute())
    return result.data[0] if result.data else None


def _save_registry(entity_type: str, external_id: str, **ids: Any) -> dict[str, Any]:
    data = {"company_id": COMPANY_ID, "entity_type": entity_type, "external_id": external_id, "payload_hash": ids.pop("payload_hash", None), "synced_at": datetime.now(timezone.utc).isoformat(), **ids}
    result = database.table("supportcandy_sync_registry").upsert(data, on_conflict="company_id,entity_type,external_id").execute()
    return result.data[0] if result.data else data


def _get_or_create_conversation(customer_id: int, ticket_id: int) -> int:
    result = (database.table("conversations").select("*").eq("customer_id", customer_id).eq("ticket_id", ticket_id).eq("channel", CHANNEL).limit(1).execute())
    if result.data:
        return int(result.data[0]["id"])
    result = database.table("conversations").insert({"customer_id": customer_id, "channel": CHANNEL, "status": "open", "ticket_id": ticket_id, "agent": "bitey", "handled_by_ai": False, "requires_human": False, "language": "pt-BR", "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()}).execute()
    return int(result.data[0]["id"])


def sync_supportcandy(limit_pages: int = 10) -> dict[str, Any]:
    client = SupportCandyClient()
    imported = {"tickets": 0, "threads": 0, "customers": 0, "skipped": 0, "errors": []}
    for page in range(1, limit_pages + 1):
        tickets = client.list_tickets(page=page)
        if not tickets:
            break
        for source in tickets:
            try:
                external_ticket_id = _text(source.get("id") or source.get("ticket_id"))
                if not external_ticket_id:
                    continue
                name = _text(source.get("name") or source.get("customer") or "Customer")
                email = _text(source.get("email"))
                customer_external = _text(source.get("customer_id") or source.get("customer")) or email
                customer = get_or_create_customer(COMPANY_ID, "", email=email, name=name, channel=CHANNEL, external_id=f"supportcandy:{customer_external}")
                if not customer:
                    raise RuntimeError("customer could not be resolved")
                imported["customers"] += 1

                reg = _registry("ticket", external_ticket_id)
                title = _text(source.get("subject") or source.get("title") or "SupportCandy request")
                description = _text(source.get("description"))
                status = _status(source.get("status"))
                payload_hash = _hash(source)
                if reg and reg.get("ticket_id"):
                    ticket_id = int(reg["ticket_id"])
                    database.table("tickets").update({"title": title, "description": description, "status": status, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", ticket_id).execute()
                    imported["skipped"] += 1
                else:
                    ticket = create_ticket(customer_id=int(customer["id"]), company_id=COMPANY_ID, title=title, description=description, language="pt-BR", ticket_type="technical_support", channel=CHANNEL)
                    if not ticket:
                        raise RuntimeError("ticket could not be created")
                    ticket_id = int(ticket["id"])
                    database.table("tickets").update({"status": status}).eq("id", ticket_id).execute()
                    _save_registry("ticket", external_ticket_id, customer_id=customer["id"], ticket_id=ticket_id, payload_hash=payload_hash)
                    imported["tickets"] += 1

                conversation_id = _get_or_create_conversation(int(customer["id"]), ticket_id)
                _save_registry("ticket_conversation", external_ticket_id, customer_id=customer["id"], ticket_id=ticket_id, conversation_id=conversation_id, payload_hash=payload_hash)

                for thread in client.get_threads(int(external_ticket_id)):
                    external_thread_id = _text(thread.get("id") or thread.get("thread_id"))
                    if not external_thread_id or _registry("thread", external_thread_id):
                        continue
                    body = _text(thread.get("body") or thread.get("content") or thread.get("description"))
                    if not body:
                        continue
                    sender = _text(thread.get("author") or thread.get("customer") or "").lower()
                    sender_type = "customer" if sender and ("customer" in sender or sender == name.lower()) else "agent"
                    msg = database.table("messages").insert({"company_id": COMPANY_ID, "customer_id": customer["id"], "conversation_id": conversation_id, "sender_type": sender_type, "message_content": body, "channel": CHANNEL, "message_type": "text", "ticket_id": ticket_id, "created_at": datetime.now(timezone.utc).isoformat()}).execute()
                    message_id = msg.data[0]["id"] if msg.data else None
                    _save_registry("thread", external_thread_id, customer_id=customer["id"], ticket_id=ticket_id, conversation_id=conversation_id, message_id=message_id, payload_hash=_hash(thread))
                    imported["threads"] += 1
            except Exception as exc:
                imported["errors"].append(f"ticket={source.get('id')}: {type(exc).__name__}")
    return imported
