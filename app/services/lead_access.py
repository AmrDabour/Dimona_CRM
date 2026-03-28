"""Shared RBAC for lead-scoped resources (leads, activities, etc.)."""

from app.core.permissions import UserRole
from app.models.lead import Lead
from app.models.user import User


def can_access_lead(lead: Lead, user: User) -> bool:
    """Whether *user* may read/update this lead (and its activities)."""
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.AGENT:
        return lead.assigned_to == user.id
    if user.role == UserRole.MANAGER:
        if user.team_id is None:
            return False
        if lead.assigned_to is None:
            return lead.team_id is not None and lead.team_id == user.team_id
        return bool(
            lead.assigned_user and lead.assigned_user.team_id == user.team_id
        )
    return False
