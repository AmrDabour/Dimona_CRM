from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import io

from app.database import get_db
from app.dependencies import get_current_user, require_roles, PaginationParams
from app.services.lead_service import LeadService
from app.services.audit_service import AuditService
from app.utils.excel import ExcelService
from app.core.permissions import UserRole
from app.core.exceptions import PermissionDeniedException
from app.models.user import User
from app.models.lead import Lead, LeadStatus
from app.models.audit_log import AuditAction
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.get("/stats")
async def get_pipeline_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get pipeline funnel statistics.
    Returns count of leads in each stage.
    RBAC-scoped: Agent sees own, Manager sees team, Admin sees all.
    """
    lead_service = LeadService(db)

    base_query = select(Lead.status, func.count(Lead.id)).where(Lead.is_deleted == False)

    if current_user.role == UserRole.AGENT:
        base_query = base_query.where(Lead.assigned_to == current_user.id)
    elif current_user.role == UserRole.MANAGER:
        team_members_query = select(User.id).where(
            User.team_id == current_user.team_id,
            User.is_deleted == False,
        )
        result = await db.execute(team_members_query)
        member_ids = [m[0] for m in result.fetchall()]
        base_query = base_query.where(Lead.assigned_to.in_(member_ids))

    base_query = base_query.group_by(Lead.status)

    result = await db.execute(base_query)
    status_counts = {row[0].value: row[1] for row in result.fetchall()}

    stages = [
        {"stage": "new", "label": "New", "count": status_counts.get("new", 0)},
        {"stage": "contacted", "label": "Contacted", "count": status_counts.get("contacted", 0)},
        {"stage": "viewing", "label": "Viewing Scheduled", "count": status_counts.get("viewing", 0)},
        {"stage": "negotiation", "label": "Negotiation", "count": status_counts.get("negotiation", 0)},
        {"stage": "won", "label": "Won", "count": status_counts.get("won", 0)},
        {"stage": "lost", "label": "Lost", "count": status_counts.get("lost", 0)},
    ]

    total = sum(s["count"] for s in stages)
    active = sum(s["count"] for s in stages if s["stage"] not in ["won", "lost"])

    return {
        "stages": stages,
        "total": total,
        "active": active,
        "conversion_rate": round((status_counts.get("won", 0) / total * 100), 2) if total > 0 else 0,
    }


@router.get("/by-stage/{status}")
async def get_leads_by_stage(
    status: LeadStatus,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
):
    """Get all leads in a specific pipeline stage."""
    lead_service = LeadService(db)
    leads, total = await lead_service.list_leads(
        current_user=current_user,
        page=pagination.page,
        page_size=pagination.page_size,
        status=status,
    )

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return {
        "items": leads,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_pages": total_pages,
    }


# Import/Export endpoints
import_export_router = APIRouter(prefix="/leads", tags=["Lead Import/Export"])


@import_export_router.post("/import")
async def import_leads(
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    source_id: Optional[UUID] = None,
):
    """
    Import leads from Excel file.
    - Admin: Can import for anyone
    - Manager: Can import for their team
    
    Required columns: Full Name, Phone
    Optional columns: Email, WhatsApp, Status, Source
    """
    default_assigned_to = None
    if current_user.role == UserRole.MANAGER:
        default_assigned_to = current_user.id

    excel_service = ExcelService(db)
    result = await excel_service.import_leads_from_excel(
        file=file,
        default_source_id=source_id,
        default_assigned_to=default_assigned_to,
    )

    audit_service = AuditService(db)
    await audit_service.log_import(
        user=current_user,
        entity_type="lead",
        new_values={"imported": result["created"], "skipped": result["skipped"]},
    )
    await db.commit()

    return result


@import_export_router.get("/export")
async def export_leads(
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: Optional[LeadStatus] = None,
    source_id: Optional[UUID] = None,
):
    """
    Export leads to Excel file.
    Admin only - Agents and Managers cannot export data.
    """
    lead_service = LeadService(db)
    leads, _ = await lead_service.list_leads(
        current_user=current_user,
        page=1,
        page_size=10000,
        status=status,
        source_id=source_id,
    )

    excel_service = ExcelService(db)
    excel_bytes = await excel_service.export_leads_to_excel(leads)

    audit_service = AuditService(db)
    await audit_service.log_export(user=current_user, entity_type="lead")
    await db.commit()

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=leads_export.xlsx"},
    )
