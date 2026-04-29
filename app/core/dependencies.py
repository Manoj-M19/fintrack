from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_subject_from_token

#  OAuth2 scheme 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ── Convenience type aliases for dependency injection ─────────────────────────
DBSession = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user_id(token: TokenDep) -> int:
    """
    Validates the Bearer token and returns the authenticated user's ID.
    Raises 401 on any token error.

    Usage:
        @router.get("/me")
        async def me(user_id: int = Depends(get_current_user_id)):
            ...
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id_str = get_subject_from_token(token, token_type="access")
        return int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception


#  Annotated shorthand used across all protected routers 
CurrentUserID = Annotated[int, Depends(get_current_user_id)]