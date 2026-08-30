"""Portal de Suporte -> BiteFixes canonical data synchronization."""
from __future__ import annotations

import os
from fastapi import APIRouter, Header, HTTPException

from app.integrations.supportcandy.client import SupportCandyConfigurationError
from app.integrations.supportcandy.sync import sync_supportcandy

router = APIRouter(prefix="/integrations/supportcandy", tags=["SupportCandy"])


def _authorized(secret: str | None) -> bool:
    expected = os.getenv("SUPPORTCANDY_SYNC_TOKEN", "").strip()
    return bool(expected and secret and secret == expected)


@router.get("/status")
def status():
    return {
        "provider": "supportcandy",
        "portal": "https://bitefixes.com/portal-de-suporte/",
        "canonical_database": "Supabase bitefixes-backed",
        "channel": "portal",
        "configured": bool(os.getenv("SUPPORTCANDY_USERNAME") and os.getenv("SUPPORTCANDY_APP_PASSWORD")),
    }


@router.post("/sync")
def sync(x_sync_token: str | None = Header(default=None, alias="X-Sync-Token")):
    if not _authorized(x_sync_token):
        raise HTTPException(status_code=401, detail="Invalid or missing sync token")
    try:
        return {"status": "success", "sync": sync_supportcandy()}
    except SupportCandyConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        print("[SUPPORTCANDY SYNC ERROR]", type(exc).__name__)
        raise HTTPException(status_code=502, detail="SupportCandy synchronization failed")
