"""Dedicated shared-secret authentication for the read-only Bitey context bridge."""
import os

from fastapi import Header, HTTPException


def require_bitey_context_key(x_bitey_context_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("BITEY_CONTEXT_API_KEY", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Bitey context integration is not configured")
    if not x_bitey_context_key or x_bitey_context_key != expected:
        raise HTTPException(status_code=401, detail="Invalid Bitey context credentials")
