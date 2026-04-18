from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

#  Password hashing 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


#  JWT token creation 
def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    payload["iat"] = datetime.now(timezone.utc)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    """
    Create a short-lived JWT access token.
    'sub' is the user ID (stored as string for JWT spec compliance).
    """
    data: dict[str, Any] = {"sub": str(subject), "type": "access"}
    if extra:
        data.update(extra)
    return _create_token(data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(subject: str | int) -> str:
    """
    Create a long-lived refresh token.
    Stored in an HttpOnly cookie in production; returned in body for API clients.
    """
    data: dict[str, Any] = {"sub": str(subject), "type": "refresh"}
    return _create_token(data, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


#  JWT token decoding 
def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT.
    Raises JWTError (caught by auth middleware) on any failure.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def get_subject_from_token(token: str, token_type: str = "access") -> str:
    """
    Extract the 'sub' claim (user ID) from a validated token.
    Raises JWTError if token is invalid or of the wrong type.
    """
    payload = decode_token(token)
    if payload.get("type") != token_type:
        raise JWTError(f"Expected token type '{token_type}'")
    sub = payload.get("sub")
    if sub is None:
        raise JWTError("Token missing 'sub' claim")
    return sub