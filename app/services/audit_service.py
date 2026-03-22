from uuid import UUID
from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog, AuditAction
from app.models.user import User


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        user: Optional[User],
        entity_type: str,
        entity_id: Optional[UUID],
        action: AuditAction,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            user_id=user.id if user else None,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(audit_log)
        await self.db.flush()

        return audit_log

    async def log_create(
        self,
        user: User,
        entity_type: str,
        entity_id: UUID,
        new_values: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        return await self.log_action(
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.CREATE,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_update(
        self,
        user: User,
        entity_type: str,
        entity_id: UUID,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        return await self.log_action(
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.UPDATE,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_delete(
        self,
        user: User,
        entity_type: str,
        entity_id: UUID,
        old_values: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        return await self.log_action(
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.DELETE,
            old_values=old_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_export(
        self,
        user: User,
        entity_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        return await self.log_action(
            user=user,
            entity_type=entity_type,
            entity_id=None,
            action=AuditAction.EXPORT,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_import(
        self,
        user: User,
        entity_type: str,
        new_values: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        return await self.log_action(
            user=user,
            entity_type=entity_type,
            entity_id=None,
            action=AuditAction.IMPORT,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )
