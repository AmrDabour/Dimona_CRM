from uuid import UUID
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.lead import Lead, LeadStatus
from app.models.user import User
from app.models.team import Team
from app.models.pipeline_history import PipelineHistory
from app.models.activity import Activity, ActivityType
from app.core.exceptions import NotFoundException, BadRequestException, PermissionDeniedException
from app.core.permissions import UserRole
from app.schemas.lead import LeadCreate, LeadUpdate, LeadStatusUpdate, LeadAssign
from app.services.gamification_service import GamificationService


class LeadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._gamification = GamificationService(db)

    async def get_lead_by_id(
        self,
        lead_id: UUID,
        current_user: User,
        include_relations: bool = False,
    ) -> Lead:
        query = select(Lead).where(Lead.id == lead_id, Lead.is_deleted == False)

        if include_relations:
            query = query.options(
                selectinload(Lead.source),
                selectinload(Lead.assigned_user),
                selectinload(Lead.requirements),
            )

        result = await self.db.execute(query)
        lead = result.scalar_one_or_none()

        if not lead:
            raise NotFoundException("Lead")

        if not self._can_access_lead(lead, current_user):
            raise PermissionDeniedException("You don't have access to this lead")

        return lead

    def _can_access_lead(self, lead: Lead, user: User) -> bool:
        if user.role == UserRole.ADMIN:
            return True
        if user.role == UserRole.MANAGER:
            return lead.assigned_user and lead.assigned_user.team_id == user.team_id
        if user.role == UserRole.AGENT:
            return lead.assigned_to == user.id
        return False

    async def list_leads(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[LeadStatus] = None,
        source_id: Optional[UUID] = None,
        assigned_to: Optional[UUID] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Lead], int]:
        query = select(Lead).where(Lead.is_deleted == False)
        query = query.options(
            selectinload(Lead.source),
            selectinload(Lead.assigned_user),
        )

        if current_user.role == UserRole.AGENT:
            query = query.where(Lead.assigned_to == current_user.id)
        elif current_user.role == UserRole.MANAGER:
            team_members_query = select(User.id).where(
                User.team_id == current_user.team_id,
                User.is_deleted == False,
            )
            team_members = await self.db.execute(team_members_query)
            member_ids = [m[0] for m in team_members.fetchall()]
            query = query.where(Lead.assigned_to.in_(member_ids))

        if status:
            query = query.where(Lead.status == status)
        if source_id:
            query = query.where(Lead.source_id == source_id)
        if assigned_to:
            query = query.where(Lead.assigned_to == assigned_to)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Lead.full_name.ilike(search_pattern),
                    Lead.phone.ilike(search_pattern),
                    Lead.email.ilike(search_pattern),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Lead.created_at.desc())

        result = await self.db.execute(query)
        leads = result.scalars().all()

        return list(leads), total

    async def create_lead(
        self,
        lead_data: LeadCreate,
        current_user: User,
    ) -> Lead:
        existing = await self.db.execute(
            select(Lead).where(
                Lead.phone == lead_data.phone,
                Lead.is_deleted == False,
            )
        )
        if existing.scalar_one_or_none():
            raise BadRequestException("Lead with this phone number already exists")

        assigned_to = lead_data.assigned_to
        if current_user.role == UserRole.AGENT:
            assigned_to = current_user.id
        elif assigned_to is None:
            assigned_to = await self._get_next_assignee(current_user)

        new_lead = Lead(
            full_name=lead_data.full_name,
            phone=lead_data.phone,
            email=lead_data.email,
            whatsapp_number=lead_data.whatsapp_number,
            source_id=lead_data.source_id,
            assigned_to=assigned_to,
            custom_fields=lead_data.custom_fields,
            notes=lead_data.notes,
            status=LeadStatus.NEW,
        )

        self.db.add(new_lead)
        await self.db.flush()

        history = PipelineHistory(
            lead_id=new_lead.id,
            changed_by=current_user.id,
            from_status=None,
            to_status=LeadStatus.NEW,
            note="Lead created",
        )
        self.db.add(history)

        await self.db.commit()
        # Return eager-loaded relations required by LeadResponse.
        return await self.get_lead_by_id(
            new_lead.id,
            current_user,
            include_relations=True,
        )

    async def _get_next_assignee(self, current_user: User) -> Optional[UUID]:
        """Round-robin assignment within the team."""
        if current_user.role == UserRole.ADMIN:
            return None

        team_id = current_user.team_id
        if not team_id:
            return current_user.id

        agents_query = select(User).where(
            User.team_id == team_id,
            User.role == UserRole.AGENT,
            User.is_active == True,
            User.is_deleted == False,
        ).order_by(User.created_at)

        result = await self.db.execute(agents_query)
        agents = result.scalars().all()

        if not agents:
            return current_user.id

        for agent in agents:
            lead_count_query = select(func.count()).select_from(Lead).where(
                Lead.assigned_to == agent.id,
                Lead.is_deleted == False,
                Lead.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.VIEWING, LeadStatus.NEGOTIATION]),
            )
            count = await self.db.scalar(lead_count_query)
            agent._lead_count = count

        agents_sorted = sorted(agents, key=lambda a: a._lead_count)
        return agents_sorted[0].id if agents_sorted else current_user.id

    async def update_lead(
        self,
        lead_id: UUID,
        lead_data: LeadUpdate,
        current_user: User,
    ) -> Lead:
        lead = await self.get_lead_by_id(lead_id, current_user, include_relations=True)

        if lead_data.full_name is not None:
            lead.full_name = lead_data.full_name
        if lead_data.phone is not None:
            existing = await self.db.execute(
                select(Lead).where(
                    Lead.phone == lead_data.phone,
                    Lead.id != lead_id,
                    Lead.is_deleted == False,
                )
            )
            if existing.scalar_one_or_none():
                raise BadRequestException("Lead with this phone number already exists")
            lead.phone = lead_data.phone
        if lead_data.email is not None:
            lead.email = lead_data.email
        if lead_data.whatsapp_number is not None:
            lead.whatsapp_number = lead_data.whatsapp_number
        if lead_data.custom_fields is not None:
            lead.custom_fields = lead_data.custom_fields
        if lead_data.notes is not None:
            lead.notes = lead_data.notes

        await self.db.commit()
        return await self.get_lead_by_id(lead_id, current_user, include_relations=True)

    async def update_lead_status(
        self,
        lead_id: UUID,
        status_data: LeadStatusUpdate,
        current_user: User,
    ) -> Lead:
        lead = await self.get_lead_by_id(lead_id, current_user, include_relations=True)

        if status_data.status == LeadStatus.LOST and not status_data.lost_reason:
            raise BadRequestException("Lost reason is required when marking a lead as lost")

        old_status = lead.status
        lead.status = status_data.status

        if status_data.status == LeadStatus.LOST:
            lead.lost_reason = status_data.lost_reason

        history = PipelineHistory(
            lead_id=lead.id,
            changed_by=current_user.id,
            from_status=old_status,
            to_status=status_data.status,
            note=status_data.note or status_data.lost_reason,
        )
        self.db.add(history)

        activity = Activity(
            lead_id=lead.id,
            user_id=current_user.id,
            type=ActivityType.STATUS_CHANGE,
            description=f"Status changed from {old_status.value} to {status_data.status.value}",
            is_completed=True,
        )
        self.db.add(activity)

        await self.db.commit()

        # ── Gamification hooks ───────────────────────────────────────
        if status_data.status == LeadStatus.NEGOTIATION:
            await self._gamification.award_points(
                current_user.id, "negotiation_reached",
                reference_id=lead.id, reference_type="lead",
            )
        elif status_data.status == LeadStatus.WON:
            intent = (lead.custom_fields or {}).get("intent", "buy")
            event = "rent_won" if intent == "rent" else "sale_won"
            await self._gamification.award_points(
                current_user.id, event,
                reference_id=lead.id, reference_type="lead",
            )
        elif status_data.status == LeadStatus.LOST and not status_data.lost_reason:
            await self._gamification.apply_penalty(
                current_user.id, "lost_no_reason",
                reference_id=lead.id, reference_type="lead",
            )
        await self.db.commit()

        return await self.get_lead_by_id(lead_id, current_user, include_relations=True)

    async def assign_lead(
        self,
        lead_id: UUID,
        assign_data: LeadAssign,
        current_user: User,
    ) -> Lead:
        if current_user.role == UserRole.AGENT:
            raise PermissionDeniedException("Agents cannot reassign leads")

        lead = await self.get_lead_by_id(lead_id, current_user, include_relations=True)

        assignee_result = await self.db.execute(
            select(User).where(
                User.id == assign_data.assigned_to,
                User.is_deleted == False,
                User.is_active == True,
            )
        )
        assignee = assignee_result.scalar_one_or_none()
        if not assignee:
            raise NotFoundException("Assignee user")

        if current_user.role == UserRole.MANAGER:
            if assignee.team_id != current_user.team_id:
                raise PermissionDeniedException("You can only assign leads to your team members")

        old_assignee_id = lead.assigned_to
        lead.assigned_to = assign_data.assigned_to

        activity = Activity(
            lead_id=lead.id,
            user_id=current_user.id,
            type=ActivityType.NOTE,
            description=f"Lead reassigned from {old_assignee_id} to {assign_data.assigned_to}",
            is_completed=True,
        )
        self.db.add(activity)

        await self.db.commit()
        return await self.get_lead_by_id(lead_id, current_user, include_relations=True)

    async def delete_lead(
        self,
        lead_id: UUID,
        current_user: User,
    ) -> None:
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("Only admins can delete leads")

        lead = await self.get_lead_by_id(lead_id, current_user)

        lead.is_deleted = True
        lead.deleted_at = datetime.now(timezone.utc)

        await self.db.commit()

    async def get_pipeline_history(
        self,
        lead_id: UUID,
        current_user: User,
    ) -> List[PipelineHistory]:
        await self.get_lead_by_id(lead_id, current_user)

        query = select(PipelineHistory).where(
            PipelineHistory.lead_id == lead_id
        ).order_by(PipelineHistory.changed_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())
