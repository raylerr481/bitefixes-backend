"""Read-only context bridge for Bitey IA Web.

This endpoint exposes only tenant-scoped enterprise context requested by Bitey.
It does not change the existing BiteFixes chat/CRM context pipeline.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database.supabase import supabase_manager
from app.security.channel_auth import require_channel_key

router = APIRouter(prefix="/bitey-context", tags=["bitey-context"], dependencies=[Depends(require_channel_key)])


def _rows(table: str, company_id: str, limit: int = 1):
    try:
        response = (
            supabase_manager.table(table)
            .select("*")
            .eq("company_id", company_id)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception:
        return []


@router.get("/company/{company_id}")
def company_context(company_id: str, include_profile: bool = Query(True)):
    company = _rows("companies", company_id)
    profile = _rows("company_ai_profiles", company_id) if include_profile else []
    if not company and not profile:
        raise HTTPException(status_code=404, detail="Company context not found")
    return {
        "source": "bitefixes_backend",
        "company_id": company_id,
        "company": company[0] if company else {},
        "profile": profile[0] if profile else {},
        "read_only": True,
    }
