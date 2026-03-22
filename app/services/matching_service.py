from uuid import UUID
from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.lead import Lead
from app.models.lead_requirement import LeadRequirement
from app.models.unit import Unit, UnitStatus
from app.models.project import Project
from app.models.lead_property_match import LeadPropertyMatch
from app.models.user import User
from app.core.exceptions import NotFoundException, PermissionDeniedException
from app.core.permissions import UserRole


class MatchingService:
    """
    Smart matching service that scores units against lead requirements.
    
    Scoring weights:
    - Budget fit: 40%
    - Location match: 30%
    - Bedrooms match: 15%
    - Area match: 15%
    """

    WEIGHT_BUDGET = 0.40
    WEIGHT_LOCATION = 0.30
    WEIGHT_BEDROOMS = 0.15
    WEIGHT_AREA = 0.15

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _verify_lead_access(self, lead_id: UUID, current_user: User) -> Lead:
        query = select(Lead).where(Lead.id == lead_id, Lead.is_deleted == False)
        query = query.options(
            selectinload(Lead.assigned_user),
            selectinload(Lead.requirements),
        )

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

    def _calculate_budget_score(
        self,
        price: Decimal,
        budget_min: Optional[Decimal],
        budget_max: Optional[Decimal],
    ) -> float:
        """Calculate how well the unit price fits the budget range."""
        if budget_min is None and budget_max is None:
            return 1.0

        if budget_min and budget_max:
            if budget_min <= price <= budget_max:
                mid_point = (budget_min + budget_max) / 2
                distance = abs(price - mid_point)
                range_half = (budget_max - budget_min) / 2
                if range_half > 0:
                    return max(0, 1 - float(distance / range_half) * 0.5)
                return 1.0
            elif price < budget_min:
                diff = (budget_min - price) / budget_min
                return max(0, 1 - float(diff))
            else:
                diff = (price - budget_max) / budget_max
                return max(0, 1 - float(diff))

        if budget_max:
            if price <= budget_max:
                return 1.0
            diff = (price - budget_max) / budget_max
            return max(0, 1 - float(diff))

        if budget_min:
            if price >= budget_min:
                return 1.0
            diff = (budget_min - price) / budget_min
            return max(0, 1 - float(diff))

        return 1.0

    def _calculate_location_score(
        self,
        unit_location: Optional[str],
        unit_city: Optional[str],
        preferred_locations: Optional[List[str]],
    ) -> float:
        """Calculate location match score."""
        if not preferred_locations:
            return 1.0

        combined_location = f"{unit_location or ''} {unit_city or ''}".lower()

        for pref in preferred_locations:
            if pref.lower() in combined_location:
                return 1.0

        for pref in preferred_locations:
            pref_lower = pref.lower()
            if any(word in combined_location for word in pref_lower.split()):
                return 0.5

        return 0.0

    def _calculate_bedrooms_score(
        self,
        unit_bedrooms: int,
        min_bedrooms: Optional[int],
    ) -> float:
        """Calculate bedrooms match score."""
        if min_bedrooms is None:
            return 1.0

        if unit_bedrooms >= min_bedrooms:
            if unit_bedrooms == min_bedrooms:
                return 1.0
            return 0.8
        else:
            diff = min_bedrooms - unit_bedrooms
            return max(0, 1 - diff * 0.3)

    def _calculate_area_score(
        self,
        unit_area: Decimal,
        min_area: Optional[Decimal],
    ) -> float:
        """Calculate area match score."""
        if min_area is None:
            return 1.0

        if unit_area >= min_area:
            return 1.0
        else:
            diff = float((min_area - unit_area) / min_area)
            return max(0, 1 - diff)

    def _calculate_property_type_multiplier(
        self,
        unit_type: str,
        required_type: Optional[str],
    ) -> float:
        """Property type must match if specified."""
        if required_type is None:
            return 1.0
        return 1.0 if unit_type == required_type else 0.0

    async def find_matches(
        self,
        lead_id: UUID,
        current_user: User,
        limit: int = 20,
    ) -> List[dict]:
        """Find and score matching units for a lead based on their requirements."""
        lead = await self._verify_lead_access(lead_id, current_user)

        if not lead.requirements:
            raise NotFoundException("Lead requirements not set")

        requirement = lead.requirements[0]

        query = select(Unit).where(
            Unit.is_deleted == False,
            Unit.status == UnitStatus.AVAILABLE,
        )
        query = query.options(
            selectinload(Unit.project).selectinload(Project.developer),
            selectinload(Unit.images),
        )

        if requirement.property_type:
            query = query.where(Unit.property_type == requirement.property_type)

        if requirement.budget_max:
            query = query.where(Unit.price <= requirement.budget_max * Decimal("1.2"))

        result = await self.db.execute(query)
        units = result.scalars().unique().all()

        scored_units = []
        for unit in units:
            budget_score = self._calculate_budget_score(
                unit.price,
                requirement.budget_min,
                requirement.budget_max,
            )

            location_score = self._calculate_location_score(
                unit.project.location if unit.project else None,
                unit.project.city if unit.project else None,
                requirement.preferred_locations,
            )

            bedrooms_score = self._calculate_bedrooms_score(
                unit.bedrooms,
                requirement.min_bedrooms,
            )

            area_score = self._calculate_area_score(
                unit.area_sqm,
                requirement.min_area_sqm,
            )

            type_multiplier = self._calculate_property_type_multiplier(
                unit.property_type.value if unit.property_type else None,
                requirement.property_type.value if requirement.property_type else None,
            )

            total_score = (
                budget_score * self.WEIGHT_BUDGET +
                location_score * self.WEIGHT_LOCATION +
                bedrooms_score * self.WEIGHT_BEDROOMS +
                area_score * self.WEIGHT_AREA
            ) * type_multiplier

            if total_score > 0:
                scored_units.append({
                    "unit": unit,
                    "relevance_score": round(total_score * 100, 2),
                    "score_breakdown": {
                        "budget": round(budget_score * 100, 2),
                        "location": round(location_score * 100, 2),
                        "bedrooms": round(bedrooms_score * 100, 2),
                        "area": round(area_score * 100, 2),
                    },
                })

        scored_units.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_units[:limit]

    async def save_match(
        self,
        lead_id: UUID,
        unit_id: UUID,
        relevance_score: Decimal,
        is_suggested: bool = False,
    ) -> LeadPropertyMatch:
        """Save a lead-unit match."""
        match = LeadPropertyMatch(
            lead_id=lead_id,
            unit_id=unit_id,
            relevance_score=relevance_score,
            is_suggested=is_suggested,
        )

        self.db.add(match)
        await self.db.commit()
        await self.db.refresh(match)

        return match

    async def mark_as_suggested(
        self,
        lead_id: UUID,
        unit_id: UUID,
        current_user: User,
    ) -> LeadPropertyMatch:
        """Mark a unit as suggested to a lead."""
        await self._verify_lead_access(lead_id, current_user)

        existing = await self.db.execute(
            select(LeadPropertyMatch).where(
                LeadPropertyMatch.lead_id == lead_id,
                LeadPropertyMatch.unit_id == unit_id,
            )
        )
        match = existing.scalar_one_or_none()

        if match:
            match.is_suggested = True
        else:
            match = LeadPropertyMatch(
                lead_id=lead_id,
                unit_id=unit_id,
                relevance_score=Decimal("0"),
                is_suggested=True,
            )
            self.db.add(match)

        await self.db.commit()
        await self.db.refresh(match)

        return match

    async def get_suggested_units(
        self,
        lead_id: UUID,
        current_user: User,
    ) -> List[LeadPropertyMatch]:
        """Get all units suggested to a lead."""
        await self._verify_lead_access(lead_id, current_user)

        result = await self.db.execute(
            select(LeadPropertyMatch)
            .where(
                LeadPropertyMatch.lead_id == lead_id,
                LeadPropertyMatch.is_suggested == True,
            )
            .options(selectinload(LeadPropertyMatch.unit))
        )

        return list(result.scalars().all())
