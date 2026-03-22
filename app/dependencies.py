from typing import Annotated
from uuid import UUID
from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import decode_token
from app.core.exceptions import CredentialsException, NotFoundException
from app.core.permissions import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    payload = decode_token(token)
    if payload is None:
        raise CredentialsException("Invalid token")

    if payload.get("type") != "access":
        raise CredentialsException("Invalid token type")

    user_id = payload.get("sub")
    if user_id is None:
        raise CredentialsException("Invalid token payload")

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise CredentialsException("Invalid user ID in token")

    result = await db.execute(
        select(User).where(User.id == user_uuid, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise CredentialsException("User not found")

    if not user.is_active:
        raise CredentialsException("User is inactive")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise CredentialsException("User is inactive")
    return current_user


def require_roles(allowed_roles: list[UserRole]):
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise CredentialsException(
                f"This action requires one of the following roles: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user
    return role_checker


RequireAdmin = Depends(require_roles([UserRole.ADMIN]))
RequireAdminOrManager = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
RequireAnyRole = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT]))


class PaginationParams:
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), 100)
        self.offset = (self.page - 1) * self.page_size
