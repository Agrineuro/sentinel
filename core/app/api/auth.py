import hashlib
import time
import hmac
import secrets
from datetime import datetime, timedelta
from uuid import uuid4

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import UserModel, UserSessionModel
from app.schemas.auth import (
    AdminPasswordReset, AdminSetup, AuthStatus, Credentials, PasswordChange, UserCreate, UserRead, UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
SESSION_COOKIE = "sentinel_session"
CSRF_COOKIE = "sentinel_csrf"
SESSION_HOURS = 12
LOGIN_WINDOW_SECONDS = 900
LOGIN_MAX_FAILURES = 10
_login_failures: dict[str, list[float]] = {}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_email(email: str) -> str:
    normalized = email.strip().casefold()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    return normalized


def _password_bytes(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        raise HTTPException(status_code=422, detail="Password must be at most 72 UTF-8 bytes")
    return encoded


def _set_session(user: UserModel, request: Request, response: Response, db: Session) -> dict:
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    db.add(UserSessionModel(
        id=f"session_{uuid4().hex}",
        user_id=user.id,
        token_hash=_digest(token),
        csrf_hash=_digest(csrf),
        expires_at=now + timedelta(hours=SESSION_HOURS),
    ))
    db.commit()
    secure = request.url.scheme == "https"
    response.set_cookie(
        SESSION_COOKIE, token, max_age=SESSION_HOURS * 3600, httponly=True,
        secure=secure, samesite="strict", path="/",
    )
    response.set_cookie(
        CSRF_COOKIE, csrf, max_age=SESSION_HOURS * 3600, httponly=False,
        secure=secure, samesite="strict", path="/",
    )
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "role": user.role, "is_active": user.is_active, "csrf_token": csrf}


def _read_user(request: Request, db: Session) -> tuple[UserModel, UserSessionModel]:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to continue")
    session = db.query(UserSessionModel).filter(
        UserSessionModel.token_hash == _digest(token),
        UserSessionModel.expires_at > datetime.utcnow(),
    ).first()
    if session is None:
        raise HTTPException(status_code=401, detail="Session expired; sign in again")
    user = db.query(UserModel).filter(UserModel.id == session.user_id, UserModel.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Account is inactive")
    if request.method.upper() not in {"GET", "HEAD", "OPTIONS"}:
        csrf_cookie = request.cookies.get(CSRF_COOKIE, "")
        csrf_header = request.headers.get("x-csrf-token", "")
        if (
            not csrf_cookie
            or not csrf_header
            or not hmac.compare_digest(csrf_cookie, csrf_header)
            or not hmac.compare_digest(_digest(csrf_cookie), session.csrf_hash)
        ):
            raise HTTPException(status_code=403, detail="Session security token is missing or invalid")
    return user, session


def require_user(request: Request, db: Session = Depends(get_db)) -> UserModel:
    user, _session = _read_user(request, db)
    return user


def require_operator(user: UserModel = Depends(require_user)) -> UserModel:
    if user.role not in {"admin", "operator"}:
        raise HTTPException(status_code=403, detail="An operator account is required for this action")
    return user


def require_admin(user: UserModel = Depends(require_user)) -> UserModel:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="An administrator account is required")
    return user


@router.get("/status", response_model=AuthStatus)
def auth_status(db: Session = Depends(get_db)):
    return {"setup_required": db.query(UserModel.id).first() is None}


@router.post("/setup")
def setup_admin(payload: AdminSetup, request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        db.execute(text("BEGIN IMMEDIATE"))
        if db.query(UserModel.id).first() is not None:
            raise HTTPException(status_code=409, detail="Sentinel already has an administrator")
        email = _normalize_email(payload.email)
        password = _password_bytes(payload.password)
        user = UserModel(
            id=f"user_{uuid4().hex}",
            email=email,
            display_name=payload.display_name.strip(),
            password_hash=bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)).decode("ascii"),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.flush()
        result = _set_session(user, request, response, db)
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.post("/login")
def login(payload: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    address = request.client.host if request.client else "unknown"
    now = time.monotonic()
    attempts = [stamp for stamp in _login_failures.get(address, []) if now - stamp < LOGIN_WINDOW_SECONDS]
    _login_failures[address] = attempts
    if len(attempts) >= LOGIN_MAX_FAILURES:
        raise HTTPException(status_code=429, detail="Too many sign-in attempts; wait 15 minutes and try again")
    email = _normalize_email(payload.email)
    user = db.query(UserModel).filter(UserModel.email == email, UserModel.is_active.is_(True)).first()
    password = _password_bytes(payload.password)
    valid = False
    if user is not None:
        try:
            valid = bcrypt.checkpw(password, user.password_hash.encode("ascii"))
        except (ValueError, TypeError):
            valid = False
    if not valid:
        attempts.append(now)
        _login_failures[address] = attempts
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    _login_failures.pop(address, None)
    return _set_session(user, request, response, db)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        db.query(UserSessionModel).filter(UserSessionModel.token_hash == _digest(token)).delete(synchronize_session=False)
        db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/", samesite="strict")
    response.delete_cookie(CSRF_COOKIE, path="/", samesite="strict")
    return {"signed_out": True}


@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user, _session = _read_user(request, db)
    csrf = request.cookies.get(CSRF_COOKIE, "")
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "role": user.role, "is_active": user.is_active, "csrf_token": csrf}


@router.post("/change-password")
def change_password(payload: PasswordChange, request: Request, response: Response, db: Session = Depends(get_db), user: UserModel = Depends(require_user)):
    password = _password_bytes(payload.current_password)
    if not bcrypt.checkpw(password, user.password_hash.encode("ascii")):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    new_password = _password_bytes(payload.new_password)
    user.password_hash = bcrypt.hashpw(new_password, bcrypt.gensalt(rounds=12)).decode("ascii")
    db.query(UserSessionModel).filter(UserSessionModel.user_id == user.id).delete(synchronize_session=False)
    response.delete_cookie(SESSION_COOKIE, path="/", samesite="strict")
    response.delete_cookie(CSRF_COOKIE, path="/", samesite="strict")
    db.commit()
    return {"password_changed": True}


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), _admin: UserModel = Depends(require_admin)):
    users = db.query(UserModel).order_by(UserModel.created_at.asc()).all()
    return [{
        "id": user.id, "email": user.email, "display_name": user.display_name,
        "role": user.role, "is_active": user.is_active, "created_at": user.created_at.isoformat(),
    } for user in users]


@router.post("/users", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _admin: UserModel = Depends(require_admin)):
    email = _normalize_email(payload.email)
    if db.query(UserModel).filter(UserModel.email == email).first():
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    password = _password_bytes(payload.password)
    user = UserModel(
        id=f"user_{uuid4().hex}", email=email, display_name=payload.display_name.strip(),
        password_hash=bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)).decode("ascii"),
        role=payload.role, is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not create account; the email may already be in use")
    return user


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db), admin: UserModel = Depends(require_admin)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Account not found")
    changes = payload.model_dump(exclude_unset=True)
    next_role = changes.get("role", user.role)
    next_active = changes.get("is_active", user.is_active)
    if user.role == "admin" and user.is_active and (next_role != "admin" or not next_active):
        other_admins = db.query(UserModel).filter(UserModel.role == "admin", UserModel.is_active.is_(True), UserModel.id != user.id).count()
        if other_admins == 0:
            raise HTTPException(status_code=409, detail="Sentinel must keep at least one active administrator")
    if user.id == admin.id and (next_role != "admin" or not next_active):
        raise HTTPException(status_code=409, detail="You cannot deactivate or remove your own administrator role")
    for key, value in changes.items():
        setattr(user, key, value)
    if not user.is_active:
        db.query(UserSessionModel).filter(UserSessionModel.user_id == user.id).delete(synchronize_session=False)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/password", status_code=204)
def reset_user_password(user_id: str, payload: AdminPasswordReset, db: Session = Depends(get_db), _admin: UserModel = Depends(require_admin)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Account not found")
    new_password = _password_bytes(payload.new_password)
    user.password_hash = bcrypt.hashpw(new_password, bcrypt.gensalt(rounds=12)).decode("ascii")
    db.query(UserSessionModel).filter(UserSessionModel.user_id == user.id).delete(synchronize_session=False)
    db.commit()
    return Response(status_code=204)
