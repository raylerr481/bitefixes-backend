"""Shared-secret authentication for server-to-server channel integrations."""
import os
from fastapi import Header, HTTPException

def require_channel_key(x_bitey_channel_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("BITEY_CHANNEL_API_KEY", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Channel integration is not configured")
    if not x_bitey_channel_key or x_bitey_channel_key != expected:
        raise HTTPException(status_code=401, detail="Invalid channel integration credentials")
