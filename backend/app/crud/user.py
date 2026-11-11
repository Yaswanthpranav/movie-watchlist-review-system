"""CRUD operations and Supabase Auth integration for the User entity."""

import uuid

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Return a User by primary key, or None if not found."""
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    """Return a User by exact username, or None if not found."""
    return db.scalar(select(User).where(User.username == username))


def get_user_by_email(db: Session, email: str) -> User | None:
    """Return a User by email address, or None if not found."""
    return db.scalar(select(User).where(User.email == email))


def get_user_by_auth_user_id(db: Session, auth_user_id: uuid.UUID) -> User | None:
    """Return a User by linked Supabase auth.users UUID."""
    return db.scalar(select(User).where(User.auth_user_id == auth_user_id))


def _resolve_login_user(
    db: Session,
    *,
    username: str | None,
    email: str | None,
) -> User | None:
    """Find user by email or username (supporting email passed in username field)."""
    if email is not None:
        return get_user_by_email(db, email)
    if username is not None:
        user = get_user_by_username(db, username)
        if user is None and "@" in username:
            user = get_user_by_email(db, username)
        return user
    return None


def _supabase_auth_headers(api_key: str) -> dict[str, str]:
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
    }
    # Supabase publishable/secret keys (sb_*) must only be sent via `apikey`, not `Authorization: Bearer`.
    if not api_key.startswith(("sb_publishable_", "sb_secret_")):
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def register_user(
    db: Session,
    *,
    username: str,
    email: str,
    password: str,
    settings: Settings,
) -> User:
    """Register a user in Supabase Auth (trigger syncs into public."user")."""
    if get_user_by_username(db, username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken.",
        )
    if get_user_by_email(db, email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    supabase_url = (settings.SUPABASE_URL or "").rstrip("/")
    api_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    if not supabase_url or not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Supabase Auth is not configured "
                "(set SUPABASE_URL and SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY)."
            ),
        )

    if settings.SUPABASE_SERVICE_ROLE_KEY:
        endpoint = f"{supabase_url}/auth/v1/admin/users"
        payload = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"username": username},
        }
    else:
        endpoint = f"{supabase_url}/auth/v1/signup"
        payload = {
            "email": email,
            "password": password,
            "data": {"username": username},
        }

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            endpoint,
            headers=_supabase_auth_headers(api_key),
            json=payload,
        )

    if resp.status_code >= 400:
        err_body = resp.json() if resp.content else {}
        err_msg = str(
            err_body.get("msg")
            or err_body.get("message")
            or err_body.get("error_description")
            or "Registration failed in Supabase Auth."
        )
        lower_err = err_msg.lower()
        if "already" in lower_err or "exists" in lower_err:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    data = resp.json()
    raw_auth_id = data.get("id") or (data.get("user") or {}).get("id")
    if not raw_auth_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase Auth did not return a user ID.",
        )

    db.expire_all()
    user = get_user_by_auth_user_id(db, uuid.UUID(str(raw_auth_id)))
    if user is None:
        user = get_user_by_email(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="User was created in Supabase Auth but not synced to public.user.",
        )
    return user


def authenticate_user(
    db: Session,
    *,
    username: str | None,
    email: str | None,
    password: str,
    settings: Settings,
) -> User | None:
    """Verify user credentials via Supabase Auth password grant."""
    user = _resolve_login_user(db, username=username, email=email)
    if user is None:
        return None

    supabase_url = (settings.SUPABASE_URL or "").rstrip("/")
    api_key = settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY
    if not supabase_url or not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth is not configured (set SUPABASE_URL and SUPABASE_ANON_KEY).",
        )

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            f"{supabase_url}/auth/v1/token?grant_type=password",
            headers=_supabase_auth_headers(api_key),
            json={"email": user.email, "password": password},
        )

    if resp.status_code == 200:
        return user

    if resp.status_code in (400, 401):
        err_body = resp.json() if resp.content else {}
        err_msg = str(
            err_body.get("error_description")
            or err_body.get("msg")
            or err_body.get("message")
            or ""
        )
        if "not confirmed" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email address is not confirmed in Supabase Auth.",
            )
        return None

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Supabase Auth verification failed.",
    )
