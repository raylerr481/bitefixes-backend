"""
BiteFixes Backend Enterprise

Customer Repository

Responsible for all database operations related to customers.
"""

from __future__ import annotations

import logging
from uuid import uuid4

from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CustomerRepository(BaseRepository):
    """
    Customer database repository.
    """

    table_name = "customers"

    # =====================================================
    # GETTERS
    # =====================================================

    def get_by_phone(
        self,
        phone: str,
    ) -> dict | None:

        return self.find_one(
            "phone",
            phone,
        )

    def get_by_email(
        self,
        email: str,
    ) -> dict | None:

        return self.find_one(
            "email",
            email,
        )

    def get_by_tax_id(
        self,
        tax_id: str,
    ) -> dict | None:

        return self.find_one(
            "tax_id",
            tax_id,
        )

    def get_by_full_name(
        self,
        full_name: str,
    ) -> list[dict]:

        return self.find_many(
            "full_name",
            full_name,
        )

    # =====================================================
    # LISTS
    # =====================================================

    def list_active(self) -> list[dict]:

        return self.find_many(
            "is_active",
            True,
        )

    def list_inactive(self) -> list[dict]:

        return self.find_many(
            "is_active",
            False,
        )

    # =====================================================
    # STATUS
    # =====================================================

    def activate(
        self,
        customer_id: int,
    ) -> dict | None:

        return self.update(
            customer_id,
            {
                "is_active": True
            },
        )

    def deactivate(
        self,
        customer_id: int,
    ) -> dict | None:

        return self.update(
            customer_id,
            {
                "is_active": False
            },
        )

    # =====================================================
    # CREATE
    # =====================================================

    def create_customer(
        self,
        company_id: int,
        full_name: str,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        tax_id: str | None = None,
        preferred_language: str = "pt",
        customer_type: str = "individual",
    ) -> dict | None:

        customer = {

            "company_id": company_id,

            "full_name": full_name,

            "phone": phone,

            "email": email,

            "address": address,

            "tax_id": tax_id,

            "preferred_language": preferred_language,

            "customer_type": customer_type,

            "is_active": True,

        }

        return self.create(customer)

    # =====================================================
    # GET OR CREATE
    # =====================================================

    def get_or_create(
        self,
        company_id: int,
        full_name: str,
        phone: str | None = None,
        email: str | None = None,
    ) -> dict | None:

        customer = None

        if phone:

            customer = self.get_by_phone(phone)

        if customer is None and email:

            customer = self.get_by_email(email)

        if customer:

            return customer

        return self.create_customer(
            company_id=company_id,
            full_name=full_name,
            phone=phone,
            email=email,
        )


customer_repository = CustomerRepository()