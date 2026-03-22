from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.lead import Lead
from app.models.lead_requirement import LeadRequirement
from app.models.user import User
from app.core.exceptions import NotFoundException, PermissionDeniedException
from app.core.permissions import UserRole
from app.schemas.lead_requirement import LeadRequirementCreate, LeadRequirementUpdate


class LeadRequirementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _verify_lead_access(self, lead_id: UUID, current_user: User) -> Lead:
        query = select(Lead).where(Lead.id == lead_id, Lead.is_deleted == False)
        query = query.options(selectinload(Lead.assigned_user))

        result = await self.db.execute(query)
        lead = result.scalar_one_or_none()

        if not lead:
            raise NotFoundException("Lead")

        if current_user.role == UserRole.AGENT and lead.assigned_to != current_user.id:
            raise PermissionDeniedException("You don't have access to this lead")

        if current_user.role == UserRole.MANAGER:
            if lead.assigned_user and lead.assigned_user.team_id != current_user.team_id:
                raise PermissionDeniedException("You don't have access to this lead")

        return lead

    async def get_requirements(self, lead_id: UUID, current_user: User) -> List[LeadRequirement]:
        await self._verify_lead_access(lead_id, current_user)

        result = await self.db.execute(
            select(LeadRequirement).where(LeadRequirement.lead_id == lead_id)
        )
        return list(result.scalars().all())

    async def create_requirement(
        self,
        lead_id: UUID,
        data: LeadRequirementCreate,
        current_user: User,
    ) -> LeadRequirement:
        await self._verify_lead_access(lead_id, current_user)

        new_requirement = LeadRequirement(
            lead_id=lead_id,
            budget_min=data.budget_min,
            budget_max=data.budget_max,
            preferred_locations=data.preferred_locations,
            min_bedrooms=data.min_bedrooms,
            min_area_sqm=data.min_area_sqm,
            property_type=data.property_type,
            notes=data.notes,
        )

        self.db.add(new_requirement)
        await self.db.commit()
        await self.db.refresh(new_requirement)

        return new_requirement

    async def update_requirement(
        self,
        requirement_id: UUID,
        data: LeadRequirementUpdate,
        current_user: User,
    ) -> LeadRequirement:
        result = await self.db.execute(
            select(LeadRequirement).where(LeadRequirement.id == requirement_id)
        )
        requirement = result.scalar_one_or_none()

        if not requirement:
            raise NotFoundException("Lead Requirement")

        await self._verify_lead_access(requirement.lead_id, current_user)

        if data.budget_min is not None:
            requirement.budget_min = data.budget_min
        if data.budget_max is not None:
            requirement.budget_max = data.budget_max
        if data.preferred_locations is not None:
            requirement.preferred_locations = data.preferred_locations
        if data.min_bedrooms is not None:
            requirement.min_bedrooms = data.min_bedrooms
        if data.min_area_sqm is not None:
            requirement.min_area_sqm = data.min_area_sqm
        if data.property_type is not None:
            requirement.property_type = data.property_type
        if data.notes is not None:
            requirement.notes = data.notes

        await self.db.commit()
        await self.db.refresh(requirement)

        return requirement

    async def delete_requirement(
        self,
        requirement_id: UUID,
        current_user: User,
    ) -> None:
        result = await self.db.execute(
            select(LeadRequirement).where(LeadRequirement.id == requirement_id)
        )
        requirement = result.scalar_one_or_none()

        if not requirement:
            raise NotFoundException("Lead Requirement")

        await self._verify_lead_access(requirement.lead_id, current_user)

        await self.db.delete(requirement)
        await self.db.commit()
