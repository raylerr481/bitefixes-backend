"""Business context diagnostics and integration endpoints."""

from fastapi import APIRouter, HTTPException

from app.schemas.business_context import BusinessContextSummary
from app.services.company_service import get_company_context

router = APIRouter(prefix="/companies", tags=["business-context"])


@router.get("/{company_id}/context", response_model=BusinessContextSummary)
def company_context(company_id: int) -> BusinessContextSummary:
    """Return the normalized Bitey business context for a company.

    This endpoint is intentionally read-only. It gives channels and integration
    tests one stable representation of the context consumed by the decision
    engine without exposing database implementation details.
    """
    context = get_company_context(company_id)
    if not context.get("company"):
        raise HTTPException(status_code=404, detail="Company not found")
    return BusinessContextSummary(company_id=company_id, **context)
