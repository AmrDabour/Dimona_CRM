from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles, PaginationParams
from app.services.inventory_service import InventoryService
from app.services.file_service import file_service
from app.core.permissions import UserRole
from app.models.user import User
from app.models.unit import UnitStatus
from app.models.lead_requirement import PropertyType
from app.schemas.inventory import (
    DeveloperCreate,
    DeveloperUpdate,
    DeveloperResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    UnitCreate,
    UnitUpdate,
    UnitResponse,
    UnitSearchParams,
    UnitImageCreate,
    UnitImageResponse,
)
from app.schemas.common import PaginatedResponse, MessageResponse

router = APIRouter(tags=["Inventory"])

# Developer endpoints
developer_router = APIRouter(prefix="/developers", tags=["Developers"])


@developer_router.get("", response_model=PaginatedResponse[DeveloperResponse])
async def list_developers(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    search: Optional[str] = None,
):
    """List all developers."""
    inventory_service = InventoryService(db)
    developers, total = await inventory_service.list_developers(
        page=pagination.page,
        page_size=pagination.page_size,
        search=search,
    )

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return PaginatedResponse(
        items=developers,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@developer_router.post("", response_model=DeveloperResponse)
async def create_developer(
    data: DeveloperCreate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new developer (Admin/Manager only)."""
    inventory_service = InventoryService(db)
    return await inventory_service.create_developer(data, current_user)


@developer_router.get("/{developer_id}", response_model=DeveloperResponse)
async def get_developer(
    developer_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get developer details."""
    inventory_service = InventoryService(db)
    return await inventory_service.get_developer_by_id(developer_id)


@developer_router.patch("/{developer_id}", response_model=DeveloperResponse)
async def update_developer(
    developer_id: UUID,
    data: DeveloperUpdate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update developer (Admin only)."""
    inventory_service = InventoryService(db)
    return await inventory_service.update_developer(developer_id, data, current_user)


@developer_router.delete("/{developer_id}", response_model=MessageResponse)
async def delete_developer(
    developer_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete developer (Admin only, soft delete)."""
    inventory_service = InventoryService(db)
    await inventory_service.delete_developer(developer_id, current_user)
    return MessageResponse(message="Developer deleted successfully")


# Project endpoints
project_router = APIRouter(prefix="/projects", tags=["Projects"])


@project_router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    developer_id: Optional[UUID] = None,
    city: Optional[str] = None,
    search: Optional[str] = None,
):
    """List all projects."""
    inventory_service = InventoryService(db)
    projects, total = await inventory_service.list_projects(
        page=pagination.page,
        page_size=pagination.page_size,
        developer_id=developer_id,
        city=city,
        search=search,
    )

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return PaginatedResponse(
        items=projects,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@project_router.post("", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new project (Admin/Manager only)."""
    inventory_service = InventoryService(db)
    return await inventory_service.create_project(data, current_user)


@project_router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get project details."""
    inventory_service = InventoryService(db)
    return await inventory_service.get_project_by_id(project_id, include_developer=True)


@project_router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update project (Admin only)."""
    inventory_service = InventoryService(db)
    return await inventory_service.update_project(project_id, data, current_user)


@project_router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete project (Admin only, soft delete)."""
    inventory_service = InventoryService(db)
    await inventory_service.delete_project(project_id, current_user)
    return MessageResponse(message="Project deleted successfully")


# Unit endpoints
unit_router = APIRouter(prefix="/units", tags=["Units"])


@unit_router.get("", response_model=PaginatedResponse[UnitResponse])
async def list_units(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    project_id: Optional[UUID] = None,
    developer_id: Optional[UUID] = None,
    property_type: Optional[PropertyType] = None,
    status: Optional[UnitStatus] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    bedrooms_min: Optional[int] = None,
    bedrooms_max: Optional[int] = None,
    area_min: Optional[float] = None,
    area_max: Optional[float] = None,
    city: Optional[str] = None,
    location: Optional[str] = None,
):
    """List and search units with filters."""
    inventory_service = InventoryService(db)

    search_params = UnitSearchParams(
        project_id=project_id,
        developer_id=developer_id,
        property_type=property_type,
        status=status,
        price_min=price_min,
        price_max=price_max,
        bedrooms_min=bedrooms_min,
        bedrooms_max=bedrooms_max,
        area_min=area_min,
        area_max=area_max,
        city=city,
        location=location,
    )

    units, total = await inventory_service.list_units(
        page=pagination.page,
        page_size=pagination.page_size,
        search_params=search_params,
    )

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return PaginatedResponse(
        items=units,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@unit_router.post("", response_model=UnitResponse)
async def create_unit(
    data: UnitCreate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new unit (Admin/Manager only)."""
    inventory_service = InventoryService(db)
    return await inventory_service.create_unit(data, current_user)


@unit_router.get("/{unit_id}", response_model=UnitResponse)
async def get_unit(
    unit_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get unit details with images."""
    inventory_service = InventoryService(db)
    return await inventory_service.get_unit_by_id(unit_id, include_relations=True)


@unit_router.patch("/{unit_id}", response_model=UnitResponse)
async def update_unit(
    unit_id: UUID,
    data: UnitUpdate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update unit (Admin only)."""
    inventory_service = InventoryService(db)
    return await inventory_service.update_unit(unit_id, data, current_user)


@unit_router.delete("/{unit_id}", response_model=MessageResponse)
async def delete_unit(
    unit_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete unit (Admin only, soft delete)."""
    inventory_service = InventoryService(db)
    await inventory_service.delete_unit(unit_id, current_user)
    return MessageResponse(message="Unit deleted successfully")


# Unit images
@unit_router.post("/{unit_id}/images", response_model=UnitImageResponse)
async def add_unit_image(
    unit_id: UUID,
    image_data: UnitImageCreate,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add image to a unit."""
    inventory_service = InventoryService(db)
    return await inventory_service.add_unit_image(unit_id, image_data, current_user)


@unit_router.post("/{unit_id}/images/upload", response_model=UnitImageResponse)
async def upload_unit_image(
    unit_id: UUID,
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    sort_order: int = 0,
):
    """Upload and add image to a unit."""
    url = await file_service.upload_file(file, folder="unit-images")

    inventory_service = InventoryService(db)
    image_data = UnitImageCreate(image_url=url, sort_order=sort_order)
    return await inventory_service.add_unit_image(unit_id, image_data, current_user)


@unit_router.delete("/images/{image_id}", response_model=MessageResponse)
async def delete_unit_image(
    image_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete unit image (Admin only)."""
    inventory_service = InventoryService(db)
    await inventory_service.delete_unit_image(image_id, current_user)
    return MessageResponse(message="Image deleted successfully")


# Include all routers
router.include_router(developer_router)
router.include_router(project_router)
router.include_router(unit_router)
