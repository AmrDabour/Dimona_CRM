from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.branch import BranchCreate, BranchUpdate, BranchResponse, BranchWithDetailsResponse
from app.dependencies import get_current_user, require_roles
from app.core.permissions import UserRole
from app.services.branch_service import BranchService

router = APIRouter(prefix="/branches", tags=["branches"])

def get_branch_service(db: AsyncSession = Depends(get_db)):
    return BranchService(db)

@router.get("/", response_model=List[BranchResponse])
async def list_branches(
    current_user: User = Depends(get_current_user),
    service: BranchService = Depends(get_branch_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    branches, _ = await service.list_branches(page=page, page_size=page_size)
    return branches

@router.get("/{branch_id}", response_model=BranchWithDetailsResponse)
async def get_branch(
    branch_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BranchService = Depends(get_branch_service),
):
    return await service.get_branch_by_id(branch_id, include_details=True)

@router.post("/", response_model=BranchResponse)
async def create_branch(
    branch_data: BranchCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    service: BranchService = Depends(get_branch_service),
):
    return await service.create_branch(branch_data, created_by=current_user)

@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: UUID,
    branch_data: BranchUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    service: BranchService = Depends(get_branch_service),
):
    return await service.update_branch(branch_id, branch_data, updated_by=current_user)

@router.delete("/{branch_id}", status_code=204)
async def delete_branch(
    branch_id: UUID,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    service: BranchService = Depends(get_branch_service),
):
    await service.delete_branch(branch_id, deleted_by=current_user)
