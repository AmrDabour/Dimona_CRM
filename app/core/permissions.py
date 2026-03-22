from enum import Enum
from typing import List
from functools import wraps

from app.core.exceptions import PermissionDeniedException


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"


class Permission(str, Enum):
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE_ALL = "user:manage_all"

    # Lead management
    LEAD_CREATE = "lead:create"
    LEAD_READ_OWN = "lead:read_own"
    LEAD_READ_TEAM = "lead:read_team"
    LEAD_READ_ALL = "lead:read_all"
    LEAD_UPDATE = "lead:update"
    LEAD_DELETE = "lead:delete"
    LEAD_ASSIGN = "lead:assign"
    LEAD_EXPORT = "lead:export"
    LEAD_IMPORT = "lead:import"

    # Inventory management
    INVENTORY_READ = "inventory:read"
    INVENTORY_CREATE = "inventory:create"
    INVENTORY_UPDATE = "inventory:update"
    INVENTORY_DELETE = "inventory:delete"

    # Reports
    REPORT_OWN = "report:own"
    REPORT_TEAM = "report:team"
    REPORT_ALL = "report:all"

    # Settings & Integrations
    SETTINGS_MANAGE = "settings:manage"
    INTEGRATIONS_MANAGE = "integrations:manage"


ROLE_PERMISSIONS: dict[UserRole, List[Permission]] = {
    UserRole.ADMIN: [
        # Full access to everything
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_MANAGE_ALL,
        Permission.LEAD_CREATE,
        Permission.LEAD_READ_OWN,
        Permission.LEAD_READ_TEAM,
        Permission.LEAD_READ_ALL,
        Permission.LEAD_UPDATE,
        Permission.LEAD_DELETE,
        Permission.LEAD_ASSIGN,
        Permission.LEAD_EXPORT,
        Permission.LEAD_IMPORT,
        Permission.INVENTORY_READ,
        Permission.INVENTORY_CREATE,
        Permission.INVENTORY_UPDATE,
        Permission.INVENTORY_DELETE,
        Permission.REPORT_OWN,
        Permission.REPORT_TEAM,
        Permission.REPORT_ALL,
        Permission.SETTINGS_MANAGE,
        Permission.INTEGRATIONS_MANAGE,
    ],
    UserRole.MANAGER: [
        # Team management, no export, no delete inventory
        Permission.USER_READ,
        Permission.LEAD_CREATE,
        Permission.LEAD_READ_OWN,
        Permission.LEAD_READ_TEAM,
        Permission.LEAD_UPDATE,
        Permission.LEAD_ASSIGN,
        Permission.LEAD_IMPORT,
        Permission.INVENTORY_READ,
        Permission.INVENTORY_CREATE,
        Permission.REPORT_OWN,
        Permission.REPORT_TEAM,
    ],
    UserRole.AGENT: [
        # Own leads only, read-only inventory, no export/import
        Permission.LEAD_CREATE,
        Permission.LEAD_READ_OWN,
        Permission.LEAD_UPDATE,
        Permission.INVENTORY_READ,
        Permission.REPORT_OWN,
    ],
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, [])


def has_any_permission(role: UserRole, permissions: List[Permission]) -> bool:
    user_permissions = ROLE_PERMISSIONS.get(role, [])
    return any(p in user_permissions for p in permissions)


def require_role(allowed_roles: List[UserRole]):
    """Dependency factory for role-based access control."""
    def checker(current_user):
        if current_user.role not in allowed_roles:
            raise PermissionDeniedException(
                f"This action requires one of the following roles: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user
    return checker


def require_permission(required_permission: Permission):
    """Dependency factory for permission-based access control."""
    def checker(current_user):
        if not has_permission(UserRole(current_user.role), required_permission):
            raise PermissionDeniedException(
                f"You don't have the required permission: {required_permission.value}"
            )
        return current_user
    return checker
