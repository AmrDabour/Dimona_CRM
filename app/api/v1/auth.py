from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import Token, UserCreate, UserResponse, RefreshTokenRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate user and return access/refresh tokens."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(form_data.username, form_data.password)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await auth_service.log_login(user, ip_address, user_agent)

    return await auth_service.create_tokens(user)


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user (public endpoint for initial setup)."""
    auth_service = AuthService(db)
    user = await auth_service.register_user(user_data)
    return user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    body: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Refresh access token using refresh token (JSON body: refresh_token)."""
    auth_service = AuthService(db)
    return await auth_service.refresh_tokens(body.refresh_token)
