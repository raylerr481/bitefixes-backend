"""Authentication helpers for the protected BiteFixes Support Portal."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from supabase import create_client

from app.config import settings

router = APIRouter(prefix="/portal/auth", tags=["Support Portal Auth"])
bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _allowed_admin_emails() -> set[str]:
    return {
        value.strip().lower()
        for value in os.getenv("PORTAL_ADMIN_EMAILS", "").split(",")
        if value.strip()
    }


def _auth_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def require_portal_admin(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        user_response = _auth_client().auth.get_user(credentials.credentials)
        user = getattr(user_response, "user", None)
        if user is None:
            raise ValueError("Invalid user")
        email = (getattr(user, "email", None) or "").strip().lower()
        allowed = _allowed_admin_emails()
        if not allowed or email not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portal administrator access required")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")


@router.post("/login")
def portal_login(payload: LoginRequest):
    allowed = _allowed_admin_emails()
    email = str(payload.email).strip().lower()
    if not allowed or email not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portal administrator access required")
    try:
        response = _auth_client().auth.sign_in_with_password({"email": email, "password": payload.password})
        session = getattr(response, "session", None)
        user = getattr(response, "user", None)
        if session is None or user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login credentials")
        return {
            "status": "success",
            "access_token": session.access_token,
            "token_type": "bearer",
            "expires_at": getattr(session, "expires_at", None),
            "user": {"id": user.id, "email": user.email},
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login credentials")


@router.get("/me")
def portal_me(user=Depends(require_portal_admin)):
    return {"status": "success", "user": {"id": user.id, "email": user.email}}
