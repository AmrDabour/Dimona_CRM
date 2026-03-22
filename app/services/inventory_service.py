from uuid import UUID
from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.developer import Developer
from app.models.project import Project
from app.models.unit import Unit, UnitStatus
from app.models.unit_image import UnitImage
from app.models.user import User
from app.models.lead_requirement import PropertyType
from app.core.exceptions import NotFoundException, BadRequestException, PermissionDeniedException
from app.core.permissions import UserRole
from app.schemas.inventory import (
    DeveloperCreate,
    DeveloperUpdate,
    ProjectCreate,
    ProjectUpdate,
    UnitCreate,
    UnitUpdate,
    UnitSearchParams,
    UnitImageCreate,
)


class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Developer operations
    async def get_developer_by_id(self, developer_id: UUID) -> Developer:
        result = await self.db.execute(
            select(Developer).where(
                Developer.id == developer_id,
                Developer.is_deleted == False,
            )
        )
        developer = result.scalar_one_or_none()
        if not developer:
            raise NotFoundException("Developer")
        return developer

    async def list_developers(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        query = select(Developer).where(Developer.is_deleted == False)

        if search:
            query = query.where(Developer.name.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Developer.name)

        result = await self.db.execute(query)
        developers = result.scalars().all()

        developers_with_count = []
        for dev in developers:
            project_count = await self.db.scalar(
                select(func.count()).select_from(Project).where(
                    Project.developer_id == dev.id,
                    Project.is_deleted == False,
                )
            )
            developers_with_count.append({
                "id": dev.id,
                "name": dev.name,
                "logo_url": dev.logo_url,
                "description": dev.description,
                "created_at": dev.created_at,
                "project_count": project_count,
            })

        return developers_with_count, total

    async def create_developer(
        self,
        data: DeveloperCreate,
        current_user: User,
    ) -> Developer:
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise PermissionDeniedException("Only admins and managers can create developers")

        new_developer = Developer(
            name=data.name,
            description=data.description,
            logo_url=data.logo_url,
        )

        self.db.add(new_developer)
        await self.db.commit()
        await self.db.refresh(new_developer)

        return new_developer

    async def update_developer(
        self,
        developer_id: UUID,
        data: DeveloperUpdate,
        current_user: User,
    ) -> Developer:
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("Only admins can update developers")

        developer = await self.get_developer_by_id(developer_id)

        if data.name is not None:
            developer.name = data.name
        if data.description is not None:
            developer.description = data.description
        if data.logo_url is not None:
            developer.logo_url = data.logo_url

        await self.db.commit()
        await self.db.refresh(developer)

        return developer

    async def delete_developer(
        self,
        developer_id: UUID,
        current_user: User,
    ) -> None:
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("Only admins can delete developers")

        developer = await self.get_developer_by_id(developer_id)

        developer.is_deleted = True
        developer.deleted_at = datetime.now(timezone.utc)

        await self.db.commit()

    # Project operations
    async def get_project_by_id(
        self,
        project_id: UUID,
        include_developer: bool = False,
    ) -> Project:
        query = select(Project).where(
            Project.id == project_id,
            Project.is_deleted == False,
        )

        if include_developer:
            query = query.options(selectinload(Project.developer))

        result = await self.db.execute(query)
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundException("Project")
        return project

    async def list_projects(
        self,
        page: int = 1,
        page_size: int = 20,
        developer_id: Optional[UUID] = None,
        city: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        query = select(Project).where(Project.is_deleted == False)
        query = query.options(selectinload(Project.developer))

        if developer_id:
            query = query.where(Project.developer_id == developer_id)
        if city:
            query = query.where(Project.city.ilike(f"%{city}%"))
        if search:
            query = query.where(
                or_(
                    Project.name.ilike(f"%{search}%"),
                    Project.location.ilike(f"%{search}%"),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Project.name)

        result = await self.db.execute(query)
        projects = result.scalars().all()

        projects_with_count = []
        for proj in projects:
            unit_count = await self.db.scalar(
                select(func.count()).select_from(Unit).where(
                    Unit.project_id == proj.id,
                    Unit.is_deleted == False,
                )
            )
            projects_with_count.append({
                "id": proj.id,
                "developer_id": proj.developer_id,
                "name": proj.name,
                "location": proj.location,
                "city": proj.city,
                "lat": proj.lat,
                "lng": proj.lng,
                "description": proj.description,
                "brochure_url": proj.brochure_url,
                "created_at": proj.created_at,
                "developer": {
                    "id": proj.developer.id,
                    "name": proj.developer.name,
                } if proj.developer else None,
                "unit_count": unit_count,
            })

        return projects_with_count, total

    async def create_project(
        self,
        data: ProjectCreate,
        current_user: User,
    ) -> Project:
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise PermissionDeniedException("Only admins and managers can create projects")

        await self.get_developer_by_id(data.developer_id)

        new_project = Project(
            developer_id=data.developer_id,
            name=data.name,
            location=data.location,
            city=data.city,
            lat=data.lat,
            lng=data.lng,
            description=data.description,
            brochure_url=data.brochure_url,
        )

        self.db.add(new_project)
        await self.db.commit()
        # Return an instance with relationships eagerly loaded to avoid
        # async lazy-load during FastAPI response serialization.
        return await self.get_project_by_id(new_project.id, include_developer=True)

    async def update_project(
        self,
        project_id: UUID,
        data: ProjectUpdate,
        current_user: User,
    ) -> Project:
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("Only admins can update projects")

        project = await self.get_project_by_id(project_id, include_developer=True)

        if data.name is not None:
            project.name = data.name
        if data.location is not None:
            project.location = data.location
        if data.city is not None:
            project.city = data.city
        if data.lat is not None:
            project.lat = data.lat
        if data.lng is not None:
            project.lng = data.lng
        if data.description is not None:
            project.description = data.description
        if data.brochure_url is not None:
            project.brochure_url = data.brochure_url

        await self.db.commit()
        # Re-fetch with eager-loaded relation for safe response serialization.
        return await self.get_project_by_id(project_id, include_developer=True)

    async def delete_project(
        self,
        project_id: UUID,
        current_user: User,
    ) -> None:
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("Only admins can delete projects")

        project = await self.get_project_by_id(project_id)

        project.is_deleted = True
        project.deleted_at = datetime.now(timezone.utc)

        await self.db.commit()

    # Unit operations
    async def get_unit_by_id(
        self,
        unit_id: UUID,
        include_relations: bool = False,
    ) -> Unit:
        query = select(Unit).where(
            Unit.id == unit_id,
            Unit.is_deleted == False,
        )

        if include_relations:
            query = query.options(
                selectinload(Unit.project).selectinload(Project.developer),
                selectinload(Unit.images),
            )

        result = await self.db.execute(query)
        unit = result.scalar_one_or_none()
        if not unit:
            raise NotFoundException("Unit")
        return unit

    async def list_units(
        self,
        page: int = 1,
        page_size: int = 20,
        search_params: Optional[UnitSearchParams] = None,
    ) -> Tuple[List[Unit], int]:
        query = select(Unit).where(Unit.is_deleted == False)
        query = query.options(
            selectinload(Unit.project),
            selectinload(Unit.images),
        )

        if search_params:
            if search_params.project_id:
                query = query.where(Unit.project_id == search_params.project_id)
            if search_params.developer_id:
                query = query.join(Project).where(Project.developer_id == search_params.developer_id)
            if search_params.property_type:
                query = query.where(Unit.property_type == search_params.property_type)
            if search_params.status:
                query = query.where(Unit.status == search_params.status)
            if search_params.price_min:
                query = query.where(Unit.price >= search_params.price_min)
            if search_params.price_max:
                query = query.where(Unit.price <= search_params.price_max)
            if search_params.bedrooms_min:
                query = query.where(Unit.bedrooms >= search_params.bedrooms_min)
            if search_params.bedrooms_max:
                query = query.where(Unit.bedrooms <= search_params.bedrooms_max)
            if search_params.area_min:
                query = query.where(Unit.area_sqm >= search_params.area_min)
            if search_params.area_max:
                query = query.where(Unit.area_sqm <= search_params.area_max)
            if search_params.city:
                query = query.join(Project, isouter=True).where(
                    Project.city.ilike(f"%{search_params.city}%")
                )
            if search_params.location:
                query = query.join(Project, isouter=True).where(
                    Project.location.ilike(f"%{search_params.location}%")
                )

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Unit.created_at.desc())

        result = await self.db.execute(query)
        units = result.scalars().unique().all()

        return list(units), total

    async def create_unit(
        self,
        data: UnitCreate,
        current_user: User,
    ) -> Unit:
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise PermissionDeniedException("Only admins and managers can create units")

        await self.get_project_by_id(data.project_id)

        new_unit = Unit(
            project_id=data.project_id,
            unit_number=data.unit_number,
            property_type=data.property_type,
            price=data.price,
            area_sqm=data.area_sqm,
            bedrooms=data.bedrooms,
            bathrooms=data.bathrooms,
            floor=data.floor,
            finishing=data.finishing,
            status=data.status,
            notes=data.notes,
            specs=data.specs,
        )

        self.db.add(new_unit)
        await self.db.commit()
        # Return eager-loaded relations required by UnitResponse
        # to avoid async lazy-load during FastAPI serialization.
        return await self.get_unit_by_id(new_unit.id, include_relations=True)

    async def update_unit(
        self,
        unit_id: UUID,
        data: UnitUpdate,
        current_user: User,
    ) -> Unit:
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("Only admins can update units")

        unit = await self.get_unit_by_id(unit_id, include_relations=True)

        if data.unit_number is not None:
            unit.unit_number = data.unit_number
        if data.property_type is not None:
            unit.property_type = data.property_type
        if data.price is not None:
            unit.price = data.price
        if data.area_sqm is not None:
            unit.area_sqm = data.area_sqm
        if data.bedrooms is not None:
            unit.bedrooms = data.bedrooms
        if data.bathrooms is not None:
            unit.bathrooms = data.bathrooms
        if data.floor is not None:
            unit.floor = data.floor
        if data.finishing is not None:
            unit.finishing = data.finishing
        if data.status is not None:
            unit.status = data.status
        if data.notes is not None:
            unit.notes = data.notes
        if data.specs is not None:
            unit.specs = data.specs

        await self.db.commit()
        # Re-fetch with needed relations for response serialization.
        return await self.get_unit_by_id(unit_id, include_relations=True)

    async def delete_unit(
        self,
        unit_id: UUID,
        current_user: User,
    ) -> None:
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("Only admins can delete units")

        unit = await self.get_unit_by_id(unit_id)

        unit.is_deleted = True
        unit.deleted_at = datetime.now(timezone.utc)

        await self.db.commit()

    # Unit images
    async def add_unit_image(
        self,
        unit_id: UUID,
        image_data: UnitImageCreate,
        current_user: User,
    ) -> UnitImage:
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise PermissionDeniedException("Only admins and managers can add unit images")

        await self.get_unit_by_id(unit_id)

        new_image = UnitImage(
            unit_id=unit_id,
            image_url=image_data.image_url,
            sort_order=image_data.sort_order,
        )

        self.db.add(new_image)
        await self.db.commit()
        await self.db.refresh(new_image)

        return new_image

    async def delete_unit_image(
        self,
        image_id: UUID,
        current_user: User,
    ) -> None:
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("Only admins can delete unit images")

        result = await self.db.execute(
            select(UnitImage).where(UnitImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        if not image:
            raise NotFoundException("Unit Image")

        await self.db.delete(image)
        await self.db.commit()
