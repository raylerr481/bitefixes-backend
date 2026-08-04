"""
Customers Router

Customer management endpoints.
"""

from fastapi import APIRouter, HTTPException

from app.services.customer_service import (
    get_or_create_customer,
    get_customer_by_whatsapp,
)

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get("/{whatsapp}")
def get_customer(whatsapp: str):

    customer = get_customer_by_whatsapp(whatsapp)

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer


@router.post("/")
def create_or_get_customer(
    whatsapp: str,
    name: str,
    company_id: int = 1
):

    customer = get_or_create_customer(
        whatsapp=whatsapp,
        name=name,
        company_id=company_id,
    )

    return customer