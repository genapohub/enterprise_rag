"""JWT + password helpers (no secrets in responses)."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import bcrypt
from jose import JWTError, jwt
from app.config import get_settings


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) > 72:
        raw = raw[:72]
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    raw = plain.encode("utf-8")
    if len(raw) > 72:
        raw = raw[:72]
    try:
        return bcrypt.checkpw(raw, hashed.encode("utf-8"))
    except ValueError:
        return False


def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> tuple[str, int]:
    settings = get_settings()
    minutes = settings.jwt_access_expire_minutes
    return create_token(user_id, "access", timedelta(minutes=minutes)), minutes * 60


def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    return create_token(user_id, "refresh", timedelta(days=settings.jwt_refresh_expire_days))


def decode_token(token: str, expected_type: Optional[str] = None) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("invalid token") from exc
    if expected_type and payload.get("type") != expected_type:
        raise ValueError("wrong token type")
    return payload
