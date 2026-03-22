from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.services.matching_service import MatchingService
from app.services.lead_requirement_service import LeadRequirementService
from app.models.user import User
from app.schemas.lead_requirement import LeadRequirementCreate, LeadRequirementUpdate, LeadRequirementResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/leads/{lead_id}", tags=["Smart Matching"])


@router.get("/requirements")
async def get_lead_requirements(
    lead_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get lead's requirements."""
    requirement_service = LeadRequirementService(db)
    requirements = await requirement_service.get_requirements(lead_id, current_user)
    return {"items": requirements}


@router.post("/requirements", response_model=LeadRequirementResponse)
async def create_lead_requirement(
    lead_id: UUID,
    data: LeadRequirementCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Set lead requirements for matching."""
    requirement_service = LeadRequirementService(db)
    return await requirement_service.create_requirement(lead_id, data, current_user)


@router.patch("/requirements/{requirement_id}", response_model=LeadRequirementResponse)
async def update_lead_requirement(
    lead_id: UUID,
    requirement_id: UUID,
    data: LeadRequirementUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update lead requirements."""
    requirement_service = LeadRequirementService(db)
    return await requirement_service.update_requirement(requirement_id, data, current_user)


@router.delete("/requirements/{requirement_id}", response_model=MessageResponse)
async def delete_lead_requirement(
    lead_id: UUID,
    requirement_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete lead requirement."""
    requirement_service = LeadRequirementService(db)
    await requirement_service.delete_requirement(requirement_id, current_user)
    return MessageResponse(message="Requirement deleted successfully")


@router.get("/matches")
async def get_lead_matches(
    lead_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 20,
):
    """
    Get smart-matched properties for a lead based on their requirements.
    
    Scoring weights:
    - Budget fit: 40%
    - Location match: 30%
    - Bedrooms match: 15%
    - Area match: 15%
    """
    matching_service = MatchingService(db)
    matches = await matching_service.find_matches(lead_id, current_user, limit=limit)

    return {
        "items": [
            {
                "unit": match["unit"],
                "relevance_score": match["relevance_score"],
                "score_breakdown": match["score_breakdown"],
            }
            for match in matches
        ],
        "total": len(matches),
    }


@router.post("/matches/{unit_id}/suggest", response_model=MessageResponse)
async def suggest_unit_to_lead(
    lead_id: UUID,
    unit_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a unit as suggested to the client."""
    matching_service = MatchingService(db)
    await matching_service.mark_as_suggested(lead_id, unit_id, current_user)
    return MessageResponse(message="Unit marked as suggested to client")


@router.get("/suggested-units")
async def get_suggested_units(
    lead_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all units that have been suggested to this lead."""
    matching_service = MatchingService(db)
    suggestions = await matching_service.get_suggested_units(lead_id, current_user)
    return {"items": suggestions, "total": len(suggestions)}
