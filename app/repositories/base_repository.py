"""
BiteFixes Backend Enterprise

Base Repository

Provides generic CRUD operations for every repository.

Author:
BiteFixes Enterprise
"""

from __future__ import annotations

from typing import Any

from app.database.supabase import supabase_manager


class BaseRepository:
    """
    Generic repository.

    Every repository inherits from this class.
    """

    table_name: str = ""

    @property
    def table(self):
        return supabase_manager.table(self.table_name)

    # =====================================================
    # READ
    # =====================================================

    def get_by_id(self, record_id: int):

        response = (
            self.table
            .select("*")
            .eq("id", record_id)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    def list(
        self,
        limit: int | None = None,
        order_by: str = "id",
        descending: bool = False,
    ):

        query = (
            self.table
            .select("*")
            .order(
                order_by,
                desc=descending,
            )
        )

        if limit:
            query = query.limit(limit)

        response = query.execute()

        return response.data or []

    # =====================================================
    # CREATE
    # =====================================================

    def create(
        self,
        data: dict[str, Any],
    ):

        response = (
            self.table
            .insert(data)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    # =====================================================
    # UPDATE
    # =====================================================

    def update(
        self,
        record_id: int,
        data: dict[str, Any],
    ):

        response = (
            self.table
            .update(data)
            .eq("id", record_id)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    # =====================================================
    # DELETE
    # =====================================================

    def delete(
        self,
        record_id: int,
    ):

        (
            self.table
            .delete()
            .eq("id", record_id)
            .execute()
        )

        return True

    # =====================================================
    # FIND
    # =====================================================

    def find_one(
        self,
        column: str,
        value: Any,
    ):

        response = (
            self.table
            .select("*")
            .eq(column, value)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    def find_many(
        self,
        column: str,
        value: Any,
    ):

        response = (
            self.table
            .select("*")
            .eq(column, value)
            .execute()
        )

        return response.data or []