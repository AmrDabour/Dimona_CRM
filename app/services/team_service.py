from uuid import UUID
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.team import Team
from app.models.user import User
from app.core.exceptions import NotFoundException, BadRequestException
from app.core.permissions import UserRole
from app.schemas.team import TeamCreate, TeamUpdate


class TeamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_team_by_id(self, team_id: UUID, include_members: bool = False) -> Team:
        query = select(Team).where(Team.id == team_id)
        if include_members:
            query = query.options(selectinload(Team.members))

        result = await self.db.execute(query)
        team = result.scalar_one_or_none()
        if not team:
            raise NotFoundException("Team")
        return team

    async def list_teams(
        self,
        page: int = 1,
        page_size: int = 20,
        include_members: bool = False,
    ) -> Tuple[List[Team], int]:
        query = select(Team)
        # TeamResponse includes members; eager-load to avoid MissingGreenlet
        # during response serialization for async sessions.
        query = query.options(selectinload(Team.members))

        count_query = select(func.count()).select_from(Team)
        total = await self.db.scalar(count_query)

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Team.created_at.desc())

        result = await self.db.execute(query)
        teams = result.scalars().all()

        return list(teams), total

    async def create_team(self, team_data: TeamCreate, created_by: User) -> Team:
        if created_by.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can create teams")

        if team_data.manager_id:
            manager_result = await self.db.execute(
                select(User).where(
                    User.id == team_data.manager_id,
                    User.is_deleted.is_(False),
                    User.role.in_([UserRole.ADMIN, UserRole.MANAGER]),
                )
            )
            if not manager_result.scalar_one_or_none():
                raise BadRequestException("Manager must be an admin or manager role user")

        new_team = Team(
            name=team_data.name,
            manager_id=team_data.manager_id,
        )

        self.db.add(new_team)
        await self.db.commit()
        return await self.get_team_by_id(new_team.id, include_members=True)

    async def update_team(
        self,
        team_id: UUID,
        team_data: TeamUpdate,
        updated_by: User,
    ) -> Team:
        if updated_by.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can update teams")

        team = await self.get_team_by_id(team_id, include_members=True)

        if team_data.name is not None:
            team.name = team_data.name

        if team_data.manager_id is not None:
            manager_result = await self.db.execute(
                select(User).where(
                    User.id == team_data.manager_id,
                    User.is_deleted.is_(False),
                    User.role.in_([UserRole.ADMIN, UserRole.MANAGER]),
                )
            )
            if not manager_result.scalar_one_or_none():
                raise BadRequestException("Manager must be an admin or manager role user")
            team.manager_id = team_data.manager_id

        await self.db.commit()
        return await self.get_team_by_id(team_id, include_members=True)

    async def delete_team(self, team_id: UUID, deleted_by: User) -> None:
        if deleted_by.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can delete teams")

        team = await self.get_team_by_id(team_id, include_members=True)

        if team.members:
            raise BadRequestException("Cannot delete team with members. Remove members first.")

        await self.db.delete(team)
        await self.db.commit()

    async def add_member_to_team(
        self,
        team_id: UUID,
        user_id: UUID,
        added_by: User,
    ) -> Team:
        if added_by.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can add team members")

        await self.get_team_by_id(team_id, include_members=True)

        user_result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_deleted.is_(False))
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User")

        user.team_id = team_id
        await self.db.commit()
        return await self.get_team_by_id(team_id, include_members=True)

    async def remove_member_from_team(
        self,
        team_id: UUID,
        user_id: UUID,
        removed_by: User,
    ) -> Team:
        if removed_by.role != UserRole.ADMIN:
            raise BadRequestException("Only admins can remove team members")

        await self.get_team_by_id(team_id, include_members=True)

        user_result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.team_id == team_id,
                User.is_deleted.is_(False),
            )
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User in this team")

        user.team_id = None
        await self.db.commit()
        return await self.get_team_by_id(team_id, include_members=True)
