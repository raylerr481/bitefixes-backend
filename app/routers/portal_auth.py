"""Authentication and authorization for the protected BiteFixes Support Portal."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import create_client

from app.config import settings
from app.database.supabase import supabase_manager

router = APIRouter(prefix="/portal/auth", tags=["Support Portal Auth"])
bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: str
    password: str


def _env_emails(name: str) -> set[str]:
    return {
        value.strip().lower()
        for value in os.getenv(name, "").split(",")
        if value.strip()
    }


def _allowed_admin_emails() -> set[str]:
    return _env_emails("PORTAL_ADMIN_EMAILS")


def _allowed_owner_emails() -> set[str]:
    return _env_emails("PORTAL_OWNER_EMAILS")


def _default_company_id() -> int:
    try:
        return int(os.getenv("PORTAL_DEFAULT_COMPANY_ID", "1"))
    except ValueError:
        return 1


def _auth_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def _person_for_email(email: str) -> dict | None:
    response = (
        supabase_manager.table("company_people")
        .select("id,company_id,full_name,email,person_type,job_title,is_active")
        .eq("email", email)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def _roles_for_person(person_id: int) -> list[dict]:
    response = (
        supabase_manager.table("company_person_roles")
        .select("role_code,role_name,is_primary,authority_level,is_active")
        .eq("company_person_id", person_id)
        .eq("is_active", True)
        .order("is_primary", desc=True)
        .order("authority_level", desc=True)
        .execute()
    )
    return response.data or []


def _context_for_email(email: str) -> dict:
    normalized = email.strip().lower()
    owner = normalized in _allowed_owner_emails()
    admin = normalized in _allowed_admin_emails()
    person = _person_for_email(normalized)

    if person:
        roles = _roles_for_person(person["id"])
        role = (roles[0].get("role_code") if roles else None) or person.get("person_type") or "worker"
        role = role.strip().lower().replace(" ", "_")
        if role in {"owner", "proprietario", "dono", "proprietário"}:
            role = "owner"
        elif role in {"admin", "administrator", "administrador", "administradora"}:
            role = "admin"
        elif role in {"technician", "técnico", "tecnico", "support", "suporte"}:
            role = "technician"
        else:
            role = "worker"
        return {
            "company_id": int(person["company_id"]),
            "role": role,
            "person": person,
            "roles": roles,
        }

    if owner or admin:
        return {
            "company_id": _default_company_id(),
            "role": "owner" if owner else "admin",
            "person": None,
            "roles": [],
        }

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="The account is authenticated but is not authorized for this Portal.",
    )


def require_portal_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        user_response = _auth_client().auth.get_user(credentials.credentials)
        user = getattr(user_response, "user", None)
        if user is None:
            raise ValueError("Invalid user")
        email = (getattr(user, "email", None) or "").strip().lower()
        context = _context_for_email(email)
        return {"user": user, **context}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")


def require_portal_admin(context=Depends(require_portal_user)):
    if context["role"] not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner/Admin access required")
    return context


@router.post("/login")
def portal_login(payload: LoginRequest):
    email = payload.email.strip().lower()
    try:
        context = _context_for_email(email)
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
            "company_id": context["company_id"],
            "role": context["role"],
            "person": context["person"],
            "roles": context["roles"],
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login credentials")


@router.get("/me")
def portal_me(context=Depends(require_portal_user)):
    user = context["user"]
    return {
        "status": "success",
        "user": {"id": user.id, "email": user.email},
        "company_id": context["company_id"],
        "role": context["role"],
        "person": context["person"],
        "roles": context["roles"],
    }
