from typing import Annotated, Optional
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.core.permissions import UserRole
from app.core.exceptions import BadRequestException, NotFoundException, PermissionDeniedException
from app.models.user import User
from app.services.gamification_service import GamificationService
from app.services.attendance_import_service import AttendanceImportService

router = APIRouter(prefix="/gamification", tags=["Gamification & Points"])


def _parse_month(month_str: Optional[str]) -> Optional[date]:
    if not month_str:
        return None
    return datetime.strptime(month_str, "%Y-%m").date().replace(day=1)


@router.get("/my-points")
async def get_my_points(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    month: Optional[str] = Query(None, description="YYYY-MM format"),
):
    svc = GamificationService(db)
    return await svc.get_user_monthly_points(current_user.id, _parse_month(month))


@router.get("/my-points/history")
async def get_my_point_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    month: Optional[str] = Query(None, description="YYYY-MM format"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    svc = GamificationService(db)
    items, total = await svc.get_point_history(
        current_user.id, _parse_month(month), page, page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/leaderboard")
async def get_leaderboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    month: Optional[str] = Query(None, description="YYYY-MM format"),
    team_id: Optional[UUID] = None,
    limit: int = Query(20, ge=1, le=100),
):
    svc = GamificationService(db)
    return await svc.get_leaderboard(_parse_month(month), team_id, limit)


@router.get("/agent/{agent_id}/points")
async def get_agent_points(
    agent_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    month: Optional[str] = Query(None, description="YYYY-MM format"),
):
    if current_user.role == UserRole.MANAGER:
        from sqlalchemy import select
        from app.models.user import User as UserModel

        agent_result = await db.execute(select(UserModel).where(UserModel.id == agent_id))
        agent = agent_result.scalar_one_or_none()
        if not agent or agent.team_id != current_user.team_id:
            raise PermissionDeniedException("You can only view your team members' points")

    svc = GamificationService(db)
    return await svc.get_user_monthly_points(agent_id, _parse_month(month))


@router.get("/agent/{agent_id}/points/history")
async def get_agent_point_history(
    agent_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    month: Optional[str] = Query(None, description="YYYY-MM format"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    if current_user.role == UserRole.MANAGER:
        from sqlalchemy import select
        from app.models.user import User as UserModel

        agent_result = await db.execute(select(UserModel).where(UserModel.id == agent_id))
        agent = agent_result.scalar_one_or_none()
        if not agent or agent.team_id != current_user.team_id:
            raise PermissionDeniedException("You can only view your team members' points")

    svc = GamificationService(db)
    items, total = await svc.get_point_history(
        agent_id, _parse_month(month), page, page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ── Admin: Rules & Tiers ────────────────────────────────────────────

@router.get("/rules")
async def get_rules(
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = GamificationService(db)
    return await svc.get_all_rules()


@router.patch("/rules/point/{rule_id}")
async def update_point_rule(
    rule_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    points: Optional[int] = None,
    is_active: Optional[bool] = None,
):
    svc = GamificationService(db)
    result = await svc.update_point_rule(rule_id, points, is_active)
    if not result:
        raise NotFoundException("Point rule")
    return result


@router.patch("/rules/penalty/{rule_id}")
async def update_penalty_rule(
    rule_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    points: Optional[int] = None,
    threshold_minutes: Optional[int] = None,
    is_active: Optional[bool] = None,
):
    svc = GamificationService(db)
    result = await svc.update_penalty_rule(rule_id, points, threshold_minutes, is_active)
    if not result:
        raise NotFoundException("Penalty rule")
    return result


@router.get("/tiers")
async def get_tiers(
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = GamificationService(db)
    return await svc.get_all_tiers()


@router.patch("/tiers/{tier_id}")
async def update_tier(
    tier_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    min_points: Optional[int] = None,
    commission_pct: Optional[float] = None,
    bonus_amount: Optional[float] = None,
):
    svc = GamificationService(db)
    result = await svc.update_tier(tier_id, min_points, commission_pct, bonus_amount)
    if not result:
        raise NotFoundException("Tier")
    return result


# ── Attendance CSV import ───────────────────────────────────────────

@router.post("/attendance/import")
async def import_attendance_csv(
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    session_date: str = Form(..., description="YYYY-MM-DD"),
    dry_run: str = Form("true"),
):
    """Upload CSV with columns الاسم/name and الحضور/attendance; apply point rules."""
    try:
        sd = datetime.strptime(session_date.strip(), "%Y-%m-%d").date()
    except ValueError as e:
        raise BadRequestException("session_date must be YYYY-MM-DD") from e

    team_id = None
    if current_user.role == UserRole.MANAGER:
        if not current_user.team_id:
            raise BadRequestException("Manager has no team assigned")
        team_id = current_user.team_id

    raw = await file.read()
    if not raw:
        raise BadRequestException("Empty file")

    dry = str(dry_run).strip().lower() in ("true", "1", "yes", "on")

    svc = AttendanceImportService(db)
    result = await svc.process(
        csv_bytes=raw,
        session_date=sd,
        dry_run=dry,
        team_id=team_id,
    )

    if result.errors:
        await db.rollback()
        return result.to_dict()

    if not dry:
        await db.commit()
    else:
        await db.rollback()

    return result.to_dict()


# ── Compliance job trigger (admin/cron) ─────────────────────────────

@router.post("/compliance-check")
async def run_compliance_check(
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Trigger weekly compliance check for all active agents."""
    from sqlalchemy import select

    agents_result = await db.execute(
        select(User).where(
            User.is_deleted.is_(False),
            User.is_active.is_(True),
            User.role.in_([UserRole.AGENT, UserRole.MANAGER]),
        )
    )
    agents = agents_result.scalars().all()

    svc = GamificationService(db)
    awarded = 0
    for agent in agents:
        txn = await svc.check_weekly_compliance(agent.id)
        if txn:
            awarded += 1

    await db.commit()
    return {"checked": len(agents), "compliance_points_awarded": awarded}
