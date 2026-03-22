from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.audit_log import AuditLog, AuditAction
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import CredentialsException, BadRequestException, ConflictException
from app.schemas.user import UserCreate, Token


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, email: str, password: str) -> User:
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise CredentialsException("Incorrect email or password")

        if not user.is_active:
            raise CredentialsException("User account is inactive")

        return user

    async def create_tokens(self, user: User) -> Token:
        token_data = {
            "sub": str(user.id),
            "role": user.role.value,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_tokens(self, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        if payload is None:
            raise CredentialsException("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise CredentialsException("Invalid token type")

        user_id = payload.get("sub")
        if user_id is None:
            raise CredentialsException("Invalid token payload")

        result = await self.db.execute(
            select(User).where(User.id == UUID(user_id), User.is_deleted == False)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise CredentialsException("User not found")

        if not user.is_active:
            raise CredentialsException("User account is inactive")

        return await self.create_tokens(user)

    async def register_user(self, user_data: UserCreate) -> User:
        result = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ConflictException("User with this email already exists")

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

    async def log_login(self, user: User, ip_address: str = None, user_agent: str = None):
        audit_log = AuditLog(
            user_id=user.id,
            entity_type="user",
            entity_id=user.id,
            action=AuditAction.LOGIN,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(audit_log)
        await self.db.commit()
