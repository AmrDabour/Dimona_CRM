"""Shared RBAC for lead-scoped resources (leads, activities, etc.)."""

from app.core.permissions import UserRole
from app.models.lead import Lead
from app.models.user import User


def can_access_lead(lead: Lead, user: User) -> bool:
    """Whether *user* may read/update this lead (and its activities)."""
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.SALES_REP:
        return lead.assigned_to == user.id
    if user.role == UserRole.SALES_MANAGER:
        if user.team_id is None:
            return False
        if lead.assigned_to is None:
            return lead.team_id is not None and lead.team_id == user.team_id
        return bool(
            lead.assigned_user and lead.assigned_user.team_id == user.team_id
        )
    if user.role == UserRole.BRANCH_MANAGER:
        if user.branch_id is None:
            return False
        if lead.assigned_to is None:
            return lead.team is not None and lead.team.branch_id == user.branch_id
        return bool(
            lead.assigned_user and lead.assigned_user.branch_id == user.branch_id
        )
    return False
