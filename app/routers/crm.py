"""CRM Core for the Bitey IA multi-tenant platform.

This layer complements the existing Customer/Conversation/Ticket portal without
replacing it. The lifecycle is Lead -> Opportunity -> Sale -> Service -> Ticket.
All records are tenant-scoped by company_id.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.database.supabase import supabase_manager
from app.routers.portal_auth import require_portal_user

router = APIRouter(prefix="/portal/crm", tags=["CRM"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _insert(table: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = supabase_manager.table(table).insert(payload).execute()
    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=500, detail=f"Could not create {table} record")
    return rows[0]


def _rows(table: str, company_id: int, *, filters: dict[str, Any] | None = None, limit: int = 100):
    query = supabase_manager.table(table).select("*").eq("company_id", company_id)
    for key, value in (filters or {}).items():
        query = query.eq(key, value)
    return query.order("updated_at", desc=True).limit(limit).execute().data or []


def _one(table: str, record_id: int, company_id: int):
    rows = _rows(table, company_id, filters={"id": record_id}, limit=1)
    if not rows:
        raise HTTPException(status_code=404, detail=f"{table[:-1].title()} not found")
    return rows[0]


class LeadCreate(BaseModel):
    customer_id: int | None = None
    conversation_id: int | None = None
    source: str = "web"
    status: str = "new"
    title: str
    description: str | None = None
    value: float | None = Field(default=None, ge=0)
    currency: str = "BRL"


class OpportunityCreate(BaseModel):
    customer_id: int
    lead_id: int | None = None
    conversation_id: int | None = None
    name: str
    stage: str = "qualification"
    status: str = "open"
    value: float | None = Field(default=None, ge=0)
    currency: str = "BRL"
    probability: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class SaleCreate(BaseModel):
    customer_id: int
    opportunity_id: int | None = None
    conversation_id: int | None = None
    service_id: int | None = None
    amount: float = Field(ge=0)
    currency: str = "BRL"
    status: str = "pending"
    reference: str | None = None
    notes: str | None = None


class ServiceCreate(BaseModel):
    customer_id: int
    sale_id: int | None = None
    ticket_id: int | None = None
    name: str
    status: str = "requested"
    description: str | None = None
    scheduled_at: str | None = None
    completed_at: str | None = None
    amount: float | None = Field(default=None, ge=0)
    currency: str = "BRL"


@router.get("/overview")
def crm_overview(context=Depends(require_portal_user)):
    company_id = context["company_id"]
    return {
        "status": "success",
        "company_id": company_id,
        "pipeline": {
            "leads": _rows("crm_leads", company_id, limit=200),
            "opportunities": _rows("crm_opportunities", company_id, limit=200),
            "sales": _rows("crm_sales", company_id, limit=200),
            "services": _rows("crm_services", company_id, limit=200),
        },
        "lifecycle": ["customer", "conversation", "lead", "opportunity", "sale", "service", "ticket"],
        "channels": ["whatsapp", "telegram", "web"],
    }


@router.get("/leads")
def list_leads(status: str | None = Query(None), limit: int = Query(100, ge=1, le=500), context=Depends(require_portal_user)):
    filters = {"status": status} if status else None
    return {"status": "success", "company_id": context["company_id"], "leads": _rows("crm_leads", context["company_id"], filters=filters, limit=limit)}


@router.post("/leads")
def create_lead(body: LeadCreate, context=Depends(require_portal_user)):
    company_id = context["company_id"]
    payload = body.model_dump(exclude_none=True) | {"company_id": company_id, "created_at": _now(), "updated_at": _now()}
    return {"status": "success", "lead": _insert("crm_leads", payload)}


@router.get("/leads/{lead_id}")
def get_lead(lead_id: int, context=Depends(require_portal_user)):
    return {"status": "success", "lead": _one("crm_leads", lead_id, context["company_id"])}


@router.get("/opportunities")
def list_opportunities(stage: str | None = Query(None), limit: int = Query(100, ge=1, le=500), context=Depends(require_portal_user)):
    filters = {"stage": stage} if stage else None
    return {"status": "success", "company_id": context["company_id"], "opportunities": _rows("crm_opportunities", context["company_id"], filters=filters, limit=limit)}


@router.post("/opportunities")
def create_opportunity(body: OpportunityCreate, context=Depends(require_portal_user)):
    company_id = context["company_id"]
    payload = body.model_dump(exclude_none=True) | {"company_id": company_id, "created_at": _now(), "updated_at": _now()}
    return {"status": "success", "opportunity": _insert("crm_opportunities", payload)}


@router.get("/sales")
def list_sales(status: str | None = Query(None), limit: int = Query(100, ge=1, le=500), context=Depends(require_portal_user)):
    filters = {"status": status} if status else None
    return {"status": "success", "company_id": context["company_id"], "sales": _rows("crm_sales", context["company_id"], filters=filters, limit=limit)}


@router.post("/sales")
def create_sale(body: SaleCreate, context=Depends(require_portal_user)):
    company_id = context["company_id"]
    payload = body.model_dump(exclude_none=True) | {"company_id": company_id, "created_at": _now(), "updated_at": _now()}
    return {"status": "success", "sale": _insert("crm_sales", payload)}


@router.get("/services")
def list_services(status: str | None = Query(None), limit: int = Query(100, ge=1, le=500), context=Depends(require_portal_user)):
    filters = {"status": status} if status else None
    return {"status": "success", "company_id": context["company_id"], "services": _rows("crm_services", context["company_id"], filters=filters, limit=limit)}


@router.post("/services")
def create_service(body: ServiceCreate, context=Depends(require_portal_user)):
    company_id = context["company_id"]
    payload = body.model_dump(exclude_none=True) | {"company_id": company_id, "created_at": _now(), "updated_at": _now()}
    return {"status": "success", "service": _insert("crm_services", payload)}
