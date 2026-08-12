"""
Customers Router

Customer management endpoints.

BiteFixes Backend V2
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.customer_service import (
    get_customer_by_phone,
    get_customer_by_channel,
    get_or_create_customer,
)


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class CustomerCreateRequest(BaseModel):
    phone: str
    name: str = "Customer"
    company_id: int = 1


# ============================================================
# GET CUSTOMER BY PHONE
# ============================================================

@router.get("/{phone}")
def get_customer(
    phone: str,
    company_id: int = Query(default=1),
):
    """
    Get a customer by phone number.
    """

    customer = get_customer_by_phone(
        phone=phone,
        company_id=company_id,
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return customer


# ============================================================
# GET CUSTOMER BY CHANNEL
# ============================================================

@router.get("/channel/{channel}/{identifier}")
def get_customer_by_external_channel(
    channel: str,
    identifier: str,
    company_id: int = Query(default=1),
):
    """
    Get a customer using an external channel identifier.
    """

    customer = get_customer_by_channel(
        channel=channel,
        value=identifier,
        company_id=company_id,
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return customer


# ============================================================
# CREATE OR GET CUSTOMER
# ============================================================

@router.post("/")
def create_or_get_customer(
    request: CustomerCreateRequest,
):
    """
    Create a customer or return an existing customer
    using the phone number.
    """

    customer = get_or_create_customer(
        company_id=request.company_id,
        phone=request.phone,
        name=request.name,
    )

    if not customer:
        raise HTTPException(
            status_code=500,
            detail="Unable to create or retrieve customer",
        )

    return customer