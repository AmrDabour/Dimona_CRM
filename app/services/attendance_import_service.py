"""Parse attendance CSV and apply gamification points via existing rules."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import UserRole
from app.models.gamification import PointTransaction
from app.models.user import User
from app.services.gamification_service import GamificationService

PRESENT_TOKENS = frozenset(
    {
        "ح",
        "h",
        "1",
        "yes",
        "y",
        "نعم",
        "present",
        "p",
        "true",
    }
)
ABSENT_TOKENS = frozenset(
    {
        "غ",
        "g",
        "0",
        "no",
        "n",
        "لا",
        "absent",
        "a",
        "false",
    }
)

NAME_HEADERS_NORM = frozenset({"الاسم", "name"})
ATT_HEADERS_NORM = frozenset({"الحضور", "attendance"})


def _norm_header(h: str) -> str:
    s = (h or "").strip()
    if s.startswith("\ufeff"):
        s = s[1:]
    return s.strip().lower()


def _norm_name(s: str) -> str:
    t = (s or "").strip()
    t = re.sub(r"\s+", " ", t)
    return t.casefold()


def _classify_attendance(raw: str) -> Literal["present", "absent", "unknown"]:
    v = (raw or "").strip().casefold()
    if v in PRESENT_TOKENS:
        return "present"
    if v in ABSENT_TOKENS:
        return "absent"
    return "unknown"


def _session_note(session_date: date) -> str:
    return f"session_date={session_date.isoformat()}"


@dataclass
class AttendanceRowOut:
    line: int
    raw_name: str
    attendance_raw: str
    status: str
    user_id: Optional[str] = None
    message: Optional[str] = None


@dataclass
class AttendanceImportResult:
    dry_run: bool
    session_date: str
    batch_id: Optional[str]
    rows: List[AttendanceRowOut] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    applied_present: int = 0
    applied_absent: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "session_date": self.session_date,
            "batch_id": self.batch_id,
            "rows": [
                {
                    "line": r.line,
                    "raw_name": r.raw_name,
                    "attendance_raw": r.attendance_raw,
                    "status": r.status,
                    "user_id": r.user_id,
                    "message": r.message,
                }
                for r in self.rows
            ],
            "summary": self.summary,
            "applied_present": self.applied_present,
            "applied_absent": self.applied_absent,
            "errors": self.errors,
        }


class AttendanceImportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _users_by_normalized_name(
        self, team_id: Optional[UUID]
    ) -> Dict[str, List[User]]:
        q = select(User).where(
            User.is_deleted.is_(False),
            User.is_active.is_(True),
            User.role.in_([UserRole.AGENT, UserRole.MANAGER]),
        )
        if team_id is not None:
            q = q.where(User.team_id == team_id)
        result = await self.db.execute(q)
        users = list(result.scalars().all())
        buckets: Dict[str, List[User]] = {}
        for u in users:
            key = _norm_name(u.full_name or "")
            if not key:
                continue
            buckets.setdefault(key, []).append(u)
        return buckets

    async def _has_session_attendance(self, user_id: UUID, session_date: date) -> bool:
        note = _session_note(session_date)
        n = await self.db.scalar(
            select(func.count())
            .select_from(PointTransaction)
            .where(
                PointTransaction.user_id == user_id,
                PointTransaction.reference_type == "attendance_import",
                PointTransaction.event_type.in_(
                    ["attendance_present", "attendance_absent"]
                ),
                PointTransaction.note == note,
            )
        )
        return bool(n and n > 0)

    def _parse_csv(self, text: str) -> tuple[List[Dict[str, str]], Optional[str], Optional[str], Optional[str]]:
        text = text.lstrip("\ufeff")
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            return [], None, None, "empty_or_invalid_csv"

        name_col: Optional[str] = None
        att_col: Optional[str] = None
        for h in reader.fieldnames:
            n = _norm_header(h)
            if n in NAME_HEADERS_NORM:
                name_col = h
            if n in ATT_HEADERS_NORM:
                att_col = h

        if not name_col or not att_col:
            return [], None, None, "missing_name_or_attendance_column"

        rows: List[Dict[str, str]] = list(reader)
        return rows, name_col, att_col, None

    async def process(
        self,
        *,
        csv_bytes: bytes,
        session_date: date,
        dry_run: bool,
        team_id: Optional[UUID],
    ) -> AttendanceImportResult:
        out = AttendanceImportResult(
            dry_run=dry_run,
            session_date=session_date.isoformat(),
            batch_id=str(uuid4()) if not dry_run else None,
        )
        try:
            text = csv_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            out.errors.append("file_must_be_utf8")
            return out

        rows_raw, name_col, att_col, err = self._parse_csv(text)
        if err:
            out.errors.append(err)
            return out

        assert name_col is not None and att_col is not None

        buckets = await self._users_by_normalized_name(team_id)
        gsvc = GamificationService(self.db)
        batch_id = uuid4()
        if not dry_run:
            out.batch_id = str(batch_id)
        note = _session_note(session_date)

        summary: Dict[str, int] = {
            "total_rows": 0,
            "present": 0,
            "absent": 0,
            "unknown": 0,
            "unmatched": 0,
            "ambiguous": 0,
            "skipped_duplicate": 0,
            "applied_present": 0,
            "applied_absent": 0,
        }

        line_base = 1  # header line
        for row in rows_raw:
            line_base += 1
            raw_name = (row.get(name_col) or "").strip()
            raw_att = (row.get(att_col) or "").strip()
            if not raw_name and not raw_att:
                continue

            summary["total_rows"] += 1

            kind = _classify_attendance(raw_att)
            if kind == "unknown":
                summary["unknown"] += 1
                out.rows.append(
                    AttendanceRowOut(
                        line=line_base,
                        raw_name=raw_name,
                        attendance_raw=raw_att,
                        status="unknown",
                        message="unrecognized_attendance_value",
                    )
                )
                continue

            key = _norm_name(raw_name)
            matches = buckets.get(key, [])
            if not matches:
                summary["unmatched"] += 1
                out.rows.append(
                    AttendanceRowOut(
                        line=line_base,
                        raw_name=raw_name,
                        attendance_raw=raw_att,
                        status="unmatched",
                        message="no_user_with_this_full_name",
                    )
                )
                continue
            if len(matches) > 1:
                summary["ambiguous"] += 1
                out.rows.append(
                    AttendanceRowOut(
                        line=line_base,
                        raw_name=raw_name,
                        attendance_raw=raw_att,
                        status="ambiguous",
                        message="multiple_users_same_name",
                    )
                )
                continue

            user = matches[0]
            uid = user.id

            if kind == "present":
                summary["present"] += 1
            else:
                summary["absent"] += 1

            dup = await self._has_session_attendance(uid, session_date)
            if dup:
                summary["skipped_duplicate"] += 1
                out.rows.append(
                    AttendanceRowOut(
                        line=line_base,
                        raw_name=raw_name,
                        attendance_raw=raw_att,
                        status="skipped_duplicate",
                        user_id=str(uid),
                        message="already_recorded_for_session_date",
                    )
                )
                continue

            if dry_run:
                out.rows.append(
                    AttendanceRowOut(
                        line=line_base,
                        raw_name=raw_name,
                        attendance_raw=raw_att,
                        status="would_apply",
                        user_id=str(uid),
                        message=kind,
                    )
                )
                continue

            txn = None
            if kind == "present":
                txn = await gsvc.award_points(
                    uid,
                    "attendance_present",
                    reference_id=batch_id,
                    reference_type="attendance_import",
                    note=note,
                )
            else:
                txn = await gsvc.apply_penalty(
                    uid,
                    "attendance_absent",
                    reference_id=batch_id,
                    reference_type="attendance_import",
                    note=note,
                )

            if txn is None:
                out.rows.append(
                    AttendanceRowOut(
                        line=line_base,
                        raw_name=raw_name,
                        attendance_raw=raw_att,
                        status="unknown",
                        user_id=str(uid),
                        message="rule_missing_or_inactive",
                    )
                )
                continue

            out.rows.append(
                AttendanceRowOut(
                    line=line_base,
                    raw_name=raw_name,
                    attendance_raw=raw_att,
                    status=kind,
                    user_id=str(uid),
                )
            )
            if kind == "present":
                summary["applied_present"] += 1
                out.applied_present += 1
            else:
                summary["applied_absent"] += 1
                out.applied_absent += 1

        out.summary = summary
        if dry_run:
            out.batch_id = None
        return out
