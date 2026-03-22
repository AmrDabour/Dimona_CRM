from uuid import UUID
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.user import User
from app.models.team import Team
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.core.permissions import UserRole
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: UUID) -> User:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User")
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        team_id: Optional[UUID] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        query = select(User).where(User.is_deleted == False)

        if team_id:
            query = query.where(User.team_id == team_id)
        if role:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(User.created_at.desc())

        result = await self.db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def create_user(self, user_data: UserCreate, created_by: User) -> User:
        if created_by.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can create users")

        existing = await self.get_user_by_email(user_data.email)
        if existing:
            raise ConflictException("User with this email already exists")

        if user_data.team_id:
            team_result = await self.db.execute(
                select(Team).where(Team.id == user_data.team_id)
            )
            if not team_result.scalar_one_or_none():
                raise NotFoundException("Team")

        new_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            phone=user_data.phone,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role,
            team_id=user_data.team_id,
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def update_user(
        self,
        user_id: UUID,
        user_data: UserUpdate,
        updated_by: User,
    ) -> User:
        user = await self.get_user_by_id(user_id)

        if updated_by.role != UserRole.ADMIN and updated_by.id != user_id:
            raise BadRequestException("You can only update your own profile")

        if user_data.email and user_data.email != user.email:
            existing = await self.get_user_by_email(user_data.email)
            if existing:
                raise ConflictException("User with this email already exists")
            user.email = user_data.email

        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.phone is not None:
            user.phone = user_data.phone

        if updated_by.role == UserRole.ADMIN:
            if user_data.role is not None:
                user.role = user_data.role
            if user_data.team_id is not None:
                user.team_id = user_data.team_id
            if user_data.is_active is not None:
                user.is_active = user_data.is_active

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def delete_user(self, user_id: UUID, deleted_by: User) -> None:
        if deleted_by.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can delete users")

        user = await self.get_user_by_id(user_id)

        if user.id == deleted_by.id:
            raise BadRequestException("You cannot delete yourself")

        user.is_deleted = True
        from datetime import datetime, timezone
        user.deleted_at = datetime.now(timezone.utc)
        user.is_active = False

        await self.db.commit()

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        user = await self.get_user_by_id(user_id)

        if not verify_password(current_password, user.hashed_password):
            raise BadRequestException("Current password is incorrect")

        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()

    async def reset_password(self, user_id: UUID, new_password: str, reset_by: User) -> None:
        if reset_by.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can reset passwords")

        user = await self.get_user_by_id(user_id)
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
