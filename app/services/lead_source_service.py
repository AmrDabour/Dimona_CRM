from uuid import UUID
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.lead_source import LeadSource
from app.models.lead import Lead
from app.models.user import User
from app.core.exceptions import NotFoundException, BadRequestException
from app.core.permissions import UserRole
from app.schemas.lead_source import LeadSourceCreate, LeadSourceUpdate


class LeadSourceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_source_by_id(self, source_id: UUID) -> LeadSource:
        result = await self.db.execute(
            select(LeadSource).where(LeadSource.id == source_id)
        )
        source = result.scalar_one_or_none()
        if not source:
            raise NotFoundException("Lead Source")
        return source

    async def list_sources(
        self,
        page: int = 1,
        page_size: int = 50,
        include_lead_count: bool = True,
    ) -> Tuple[List[dict], int]:
        query = select(LeadSource)

        count_query = select(func.count()).select_from(LeadSource)
        total = await self.db.scalar(count_query)

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(LeadSource.name)

        result = await self.db.execute(query)
        sources = result.scalars().all()

        sources_with_count = []
        for source in sources:
            source_dict = {
                "id": source.id,
                "name": source.name,
                "campaign_name": source.campaign_name,
                "campaign_cost": source.campaign_cost,
                "created_at": source.created_at,
            }

            if include_lead_count:
                lead_count_query = select(func.count()).select_from(Lead).where(
                    Lead.source_id == source.id,
                    Lead.is_deleted == False,
                )
                lead_count = await self.db.scalar(lead_count_query)
                source_dict["lead_count"] = lead_count

            sources_with_count.append(source_dict)

        return sources_with_count, total

    async def create_source(
        self,
        source_data: LeadSourceCreate,
        current_user: User,
    ) -> LeadSource:
        if current_user.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can create lead sources")

        new_source = LeadSource(
            name=source_data.name,
            campaign_name=source_data.campaign_name,
            campaign_cost=source_data.campaign_cost,
        )

        self.db.add(new_source)
        await self.db.commit()
        await self.db.refresh(new_source)

        return new_source

    async def update_source(
        self,
        source_id: UUID,
        source_data: LeadSourceUpdate,
        current_user: User,
    ) -> LeadSource:
        if current_user.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can update lead sources")

        source = await self.get_source_by_id(source_id)

        if source_data.name is not None:
            source.name = source_data.name
        if source_data.campaign_name is not None:
            source.campaign_name = source_data.campaign_name
        if source_data.campaign_cost is not None:
            source.campaign_cost = source_data.campaign_cost

        await self.db.commit()
        await self.db.refresh(source)

        return source

    async def delete_source(
        self,
        source_id: UUID,
        current_user: User,
    ) -> None:
        if current_user.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can delete lead sources")

        source = await self.get_source_by_id(source_id)

        lead_count_query = select(func.count()).select_from(Lead).where(
            Lead.source_id == source_id,
            Lead.is_deleted == False,
        )
        lead_count = await self.db.scalar(lead_count_query)

        if lead_count > 0:
            raise BadRequestException(
                f"Cannot delete source with {lead_count} associated leads. "
                "Reassign leads first."
            )

        await self.db.delete(source)
        await self.db.commit()
