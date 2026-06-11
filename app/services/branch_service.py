from uuid import UUID
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.branch import Branch
from app.models.user import User
from app.core.exceptions import NotFoundException, BadRequestException
from app.core.permissions import UserRole
from app.schemas.branch import BranchCreate, BranchUpdate

class BranchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_branch_by_id(self, branch_id: UUID, include_details: bool = False) -> Branch:
        query = select(Branch).where(Branch.id == branch_id, Branch.is_deleted.is_(False))
        if include_details:
            query = query.options(
                selectinload(Branch.manager),
                selectinload(Branch.teams),
                selectinload(Branch.users)
            )

        result = await self.db.execute(query)
        branch = result.scalar_one_or_none()
        if not branch:
            raise NotFoundException("Branch")
        return branch

    async def list_branches(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Branch], int]:
        query = select(Branch).where(Branch.is_deleted.is_(False))
        
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Branch.created_at.desc())

        result = await self.db.execute(query)
        branches = result.scalars().all()

        return list(branches), total

    async def create_branch(self, branch_data: BranchCreate, created_by: User) -> Branch:
        if created_by.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can create branches")

        # Check existing branch name
        existing = await self.db.execute(select(Branch).where(Branch.name == branch_data.name, Branch.is_deleted.is_(False)))
        if existing.scalar_one_or_none():
            raise BadRequestException("Branch with this name already exists")

        if branch_data.manager_id:
            manager_result = await self.db.execute(
                select(User).where(
                    User.id == branch_data.manager_id,
                    User.is_deleted.is_(False),
                    User.role.in_([UserRole.ADMIN, UserRole.BRANCH_MANAGER]),
                )
            )
            if not manager_result.scalar_one_or_none():
                raise BadRequestException("Manager must be an admin or branch_manager role")

        new_branch = Branch(
            name=branch_data.name,
            location=branch_data.location,
            manager_id=branch_data.manager_id,
        )

        self.db.add(new_branch)
        await self.db.commit()
        await self.db.refresh(new_branch)
        return new_branch

    async def update_branch(
        self,
        branch_id: UUID,
        branch_data: BranchUpdate,
        updated_by: User,
    ) -> Branch:
        if updated_by.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can update branches")

        branch = await self.get_branch_by_id(branch_id)

        update_data = branch_data.model_dump(exclude_unset=True)
        if "name" in update_data:
            existing = await self.db.execute(
                select(Branch).where(Branch.name == update_data["name"], Branch.id != branch_id, Branch.is_deleted.is_(False))
            )
            if existing.scalar_one_or_none():
                raise BadRequestException("Branch with this name already exists")
            branch.name = update_data["name"]

        if "location" in update_data:
            branch.location = update_data["location"]

        if "manager_id" in update_data:
            if update_data["manager_id"]:
                manager_result = await self.db.execute(
                    select(User).where(
                        User.id == update_data["manager_id"],
                        User.is_deleted.is_(False),
                        User.role.in_([UserRole.ADMIN, UserRole.BRANCH_MANAGER]),
                    )
                )
                if not manager_result.scalar_one_or_none():
                    raise BadRequestException("Manager must be an admin or branch_manager role")
            branch.manager_id = update_data["manager_id"]

        await self.db.commit()
        await self.db.refresh(branch)
        return branch

    async def delete_branch(self, branch_id: UUID, deleted_by: User) -> None:
        if deleted_by.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can delete branches")

        branch = await self.get_branch_by_id(branch_id, include_details=True)

        if branch.teams or branch.users:
            raise BadRequestException("Cannot delete branch with assigned teams or users")

        branch.is_deleted = True
        await self.db.commit()
