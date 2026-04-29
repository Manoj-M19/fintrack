from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUserID
from app.schemas.auth import LoginRequest, LoginResponse, RefreshRequest, TokenResponse
from app.schemas.user import UserRegister, UserResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).register(data)


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).login(data.email, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).refresh(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: CurrentUserID,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).get_me(user_id)