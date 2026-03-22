from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.redis import redis_client
from app.models.activity import Activity
from app.models.gamification import (
    PenaltyRule,
    PointRule,
    PointTransaction,
    TierConfig,
    UserPointsSummary,
)
from app.models.user import User


def _current_month() -> date:
    today = datetime.now(timezone.utc).date()
    return today.replace(day=1)


CATEGORY_FIELD = {
    "activity": "activity_points",
    "compliance": "compliance_points",
    "conversion": "conversion_points",
    "penalty": "penalty_points",
}


class GamificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Core point operations ────────────────────────────────────────

    async def award_points(
        self,
        user_id: UUID,
        event_type: str,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
        note: str | None = None,
    ) -> PointTransaction | None:
        rule = await self.db.scalar(
            select(PointRule).where(PointRule.event_type == event_type, PointRule.is_active.is_(True))
        )
        if not rule:
            return None

        month = _current_month()
        txn = PointTransaction(
            user_id=user_id,
            rule_id=rule.id,
            points=rule.points,
            event_type=event_type,
            reference_id=reference_id,
            reference_type=reference_type,
            note=note,
            period_month=month,
        )
        self.db.add(txn)
        await self._upsert_summary(user_id, month, rule.points, rule.category)
        await self.db.flush()
        await self._invalidate_caches(user_id, month)
        return txn

    async def apply_penalty(
        self,
        user_id: UUID,
        event_type: str,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
        note: str | None = None,
    ) -> PointTransaction | None:
        rule = await self.db.scalar(
            select(PenaltyRule).where(PenaltyRule.event_type == event_type, PenaltyRule.is_active.is_(True))
        )
        if not rule:
            return None

        month = _current_month()
        txn = PointTransaction(
            user_id=user_id,
            penalty_rule_id=rule.id,
            points=rule.points,
            event_type=event_type,
            reference_id=reference_id,
            reference_type=reference_type,
            note=note,
            period_month=month,
        )
        self.db.add(txn)
        await self._upsert_summary(user_id, month, rule.points, "penalty")
        await self.db.flush()
        await self._invalidate_caches(user_id, month)
        return txn

    # ── Summary upsert ───────────────────────────────────────────────

    async def _upsert_summary(
        self, user_id: UUID, month: date, points: int, category: str
    ) -> None:
        summary = await self.db.scalar(
            select(UserPointsSummary).where(
                UserPointsSummary.user_id == user_id,
                UserPointsSummary.month == month,
            )
        )
        cat_field = CATEGORY_FIELD.get(category, "activity_points")

        if summary:
            summary.total_points += points
            setattr(summary, cat_field, getattr(summary, cat_field) + points)
        else:
            summary = UserPointsSummary(
                user_id=user_id,
                month=month,
                total_points=points,
                **{cat_field: points},
            )
            self.db.add(summary)

    # ── Read helpers ─────────────────────────────────────────────────

    async def get_user_monthly_points(
        self, user_id: UUID, month: date | None = None
    ) -> Dict[str, Any]:
        month = month or _current_month()
        summary = await self.db.scalar(
            select(UserPointsSummary).where(
                UserPointsSummary.user_id == user_id,
                UserPointsSummary.month == month,
            )
        )
        tier = await self._resolve_tier(summary.total_points if summary else 0)
        rank = await self._get_rank(user_id, month)

        return {
            "user_id": str(user_id),
            "month": month.isoformat(),
            "total_points": summary.total_points if summary else 0,
            "activity_points": summary.activity_points if summary else 0,
            "compliance_points": summary.compliance_points if summary else 0,
            "conversion_points": summary.conversion_points if summary else 0,
            "penalty_points": summary.penalty_points if summary else 0,
            "tier": tier,
            "rank": rank,
        }

    async def get_leaderboard(
        self,
        month: date | None = None,
        team_id: UUID | None = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        month = month or _current_month()

        cache_key = f"leaderboard:{month.isoformat()}:{team_id or 'all'}:{limit}"
        cached = await redis_client.get_json(cache_key)
        if cached:
            return cached

        query = (
            select(UserPointsSummary, User.full_name, User.email)
            .join(User, User.id == UserPointsSummary.user_id)
            .where(
                UserPointsSummary.month == month,
                User.is_deleted.is_(False),
                User.is_active.is_(True),
            )
        )
        if team_id:
            query = query.where(User.team_id == team_id)

        query = query.order_by(UserPointsSummary.total_points.desc()).limit(limit)
        result = await self.db.execute(query)
        rows = result.all()

        tiers = await self._get_all_tiers_sorted()
        entries: List[Dict[str, Any]] = []
        for rank, (summary, name, email) in enumerate(rows, start=1):
            entries.append({
                "rank": rank,
                "user_id": str(summary.user_id),
                "full_name": name,
                "email": email,
                "total_points": summary.total_points,
                "activity_points": summary.activity_points,
                "compliance_points": summary.compliance_points,
                "conversion_points": summary.conversion_points,
                "penalty_points": summary.penalty_points,
                "tier": self._tier_for_points(summary.total_points, tiers),
            })

        await redis_client.set_json(cache_key, entries, expire=300)
        return entries

    async def get_point_history(
        self,
        user_id: UUID,
        month: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        month = month or _current_month()
        base = select(PointTransaction).where(
            PointTransaction.user_id == user_id,
            PointTransaction.period_month == month,
        )
        total = await self.db.scalar(select(func.count()).select_from(base.subquery()))

        query = (
            base.order_by(PointTransaction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        txns = result.scalars().all()

        items = [
            {
                "id": str(t.id),
                "points": t.points,
                "event_type": t.event_type,
                "reference_id": str(t.reference_id) if t.reference_id else None,
                "reference_type": t.reference_type,
                "note": t.note,
                "created_at": t.created_at.isoformat(),
            }
            for t in txns
        ]
        return items, total or 0

    # ── Tier helpers ─────────────────────────────────────────────────

    async def _resolve_tier(self, points: int) -> Dict[str, Any]:
        tiers = await self._get_all_tiers_sorted()
        return self._tier_for_points(points, tiers)

    async def _get_all_tiers_sorted(self) -> List[TierConfig]:
        result = await self.db.execute(
            select(TierConfig).order_by(TierConfig.sort_order.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def _tier_for_points(points: int, tiers: List[TierConfig]) -> Dict[str, Any]:
        for t in tiers:
            if points >= t.min_points:
                return {
                    "name": t.name,
                    "min_points": t.min_points,
                    "commission_pct": float(t.commission_pct),
                    "bonus_amount": float(t.bonus_amount),
                }
        if tiers:
            last = tiers[-1]
            return {
                "name": last.name,
                "min_points": last.min_points,
                "commission_pct": float(last.commission_pct),
                "bonus_amount": float(last.bonus_amount),
            }
        return {"name": "bronze", "min_points": 0, "commission_pct": 15.0, "bonus_amount": 0.0}

    async def _get_rank(self, user_id: UUID, month: date) -> int:
        subq = (
            select(
                UserPointsSummary.user_id,
                func.rank().over(order_by=UserPointsSummary.total_points.desc()).label("rnk"),
            )
            .where(UserPointsSummary.month == month)
            .subquery()
        )
        result = await self.db.scalar(
            select(subq.c.rnk).where(subq.c.user_id == user_id)
        )
        return result or 0

    # ── Compliance checks ────────────────────────────────────────────

    async def check_weekly_compliance(self, user_id: UUID) -> PointTransaction | None:
        now = datetime.now(timezone.utc)
        overdue_count = await self.db.scalar(
            select(func.count(Activity.id)).where(
                Activity.user_id == user_id,
                Activity.is_completed.is_(False),
                Activity.scheduled_at.isnot(None),
                Activity.scheduled_at < now,
            )
        )
        if overdue_count == 0:
            return await self.award_points(
                user_id, "no_overdue_weekly", note="Weekly compliance: zero overdue tasks"
            )
        return None

    async def check_slow_response_penalty(
        self, lead_id: UUID, assigned_to: UUID, lead_created_at: datetime
    ) -> PointTransaction | None:
        rule = await self.db.scalar(
            select(PenaltyRule).where(
                PenaltyRule.event_type == "slow_response",
                PenaltyRule.is_active.is_(True),
            )
        )
        if not rule or not rule.threshold_minutes:
            return None

        first_activity = await self.db.scalar(
            select(Activity.created_at)
            .where(Activity.lead_id == lead_id, Activity.user_id == assigned_to)
            .order_by(Activity.created_at.asc())
        )

        if first_activity:
            diff_minutes = (first_activity - lead_created_at).total_seconds() / 60
            if diff_minutes > rule.threshold_minutes:
                return await self.apply_penalty(
                    assigned_to,
                    "slow_response",
                    reference_id=lead_id,
                    reference_type="lead",
                    note=f"Response took {int(diff_minutes)} min (threshold: {rule.threshold_minutes} min)",
                )
        return None

    # ── Admin CRUD ───────────────────────────────────────────────────

    async def get_all_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        pr = await self.db.execute(select(PointRule).order_by(PointRule.event_type))
        point_rules = [
            {
                "id": str(r.id),
                "event_type": r.event_type,
                "points": r.points,
                "category": r.category,
                "description": r.description,
                "is_active": r.is_active,
            }
            for r in pr.scalars().all()
        ]
        pen = await self.db.execute(select(PenaltyRule).order_by(PenaltyRule.event_type))
        penalty_rules = [
            {
                "id": str(r.id),
                "event_type": r.event_type,
                "points": r.points,
                "threshold_minutes": r.threshold_minutes,
                "description": r.description,
                "is_active": r.is_active,
            }
            for r in pen.scalars().all()
        ]
        return {"point_rules": point_rules, "penalty_rules": penalty_rules}

    async def update_point_rule(
        self, rule_id: UUID, points: int | None = None, is_active: bool | None = None
    ) -> Dict[str, Any] | None:
        rule = await self.db.scalar(select(PointRule).where(PointRule.id == rule_id))
        if not rule:
            return None
        if points is not None:
            rule.points = points
        if is_active is not None:
            rule.is_active = is_active
        await self.db.commit()
        return {
            "id": str(rule.id),
            "event_type": rule.event_type,
            "points": rule.points,
            "category": rule.category,
            "description": rule.description,
            "is_active": rule.is_active,
        }

    async def update_penalty_rule(
        self,
        rule_id: UUID,
        points: int | None = None,
        threshold_minutes: int | None = None,
        is_active: bool | None = None,
    ) -> Dict[str, Any] | None:
        rule = await self.db.scalar(select(PenaltyRule).where(PenaltyRule.id == rule_id))
        if not rule:
            return None
        if points is not None:
            rule.points = points
        if threshold_minutes is not None:
            rule.threshold_minutes = threshold_minutes
        if is_active is not None:
            rule.is_active = is_active
        await self.db.commit()
        return {
            "id": str(rule.id),
            "event_type": rule.event_type,
            "points": rule.points,
            "threshold_minutes": rule.threshold_minutes,
            "description": rule.description,
            "is_active": rule.is_active,
        }

    async def get_all_tiers(self) -> List[Dict[str, Any]]:
        result = await self.db.execute(select(TierConfig).order_by(TierConfig.sort_order))
        return [
            {
                "id": str(t.id),
                "name": t.name,
                "min_points": t.min_points,
                "commission_pct": float(t.commission_pct),
                "bonus_amount": float(t.bonus_amount),
                "perks": t.perks,
                "sort_order": t.sort_order,
            }
            for t in result.scalars().all()
        ]

    async def update_tier(
        self,
        tier_id: UUID,
        min_points: int | None = None,
        commission_pct: float | None = None,
        bonus_amount: float | None = None,
    ) -> Dict[str, Any] | None:
        tier = await self.db.scalar(select(TierConfig).where(TierConfig.id == tier_id))
        if not tier:
            return None
        if min_points is not None:
            tier.min_points = min_points
        if commission_pct is not None:
            tier.commission_pct = Decimal(str(commission_pct))
        if bonus_amount is not None:
            tier.bonus_amount = Decimal(str(bonus_amount))
        await self.db.commit()
        return {
            "id": str(tier.id),
            "name": tier.name,
            "min_points": tier.min_points,
            "commission_pct": float(tier.commission_pct),
            "bonus_amount": float(tier.bonus_amount),
            "perks": tier.perks,
            "sort_order": tier.sort_order,
        }

    # ── Cache invalidation ───────────────────────────────────────────

    @staticmethod
    async def _invalidate_caches(user_id: UUID, month: date) -> None:
        try:
            await redis_client.delete(f"dashboard:{user_id}:agent")
            await redis_client.delete(f"dashboard:{user_id}:manager")
            await redis_client.delete(f"dashboard:{user_id}:admin")
            await redis_client.delete(f"leaderboard:{month.isoformat()}:all:20")
        except Exception:
            pass
