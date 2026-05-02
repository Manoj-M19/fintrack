from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_subject_from_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginResponse, TokenResponse
from app.schemas.user import UserRegister, UserResponse
from fastapi import HTTPException, status
from jose import JWTError


class AuthService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, data: UserRegister) -> UserResponse:
        # Check if email already exists
        if await self.user_repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered.",
            )

        # Create user
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        user = await self.user_repo.create(user)
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> LoginResponse:
        # Find user
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated.",
            )

        tokens = TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )
        return LoginResponse(
            tokens=tokens,
            user=UserResponse.model_validate(user),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )
        try:
            user_id = get_subject_from_token(refresh_token, token_type="refresh")
        except JWTError:
            raise credentials_exception

        user = await self.user_repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise credentials_exception

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def get_me(self, user_id: int) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return UserResponse.model_validate(user)