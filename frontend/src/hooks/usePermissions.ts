import { useAuthStore, type UserRole } from "@/stores/authStore";

export function usePermissions() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role;

  const is = (r: UserRole) => role === r;

  return {
    role,
    isAdmin: is("admin"),
    isManager: is("manager"),
    isAgent: is("agent"),

    // Lead permissions
    canCreateLead: true,
    canDeleteLead: is("admin"),
    canExportLeads: is("admin"),
    canImportLeads: is("admin") || is("manager"),
    canAssignLead: is("admin") || is("manager"),
    canReadAllLeads: is("admin"),
    canReadTeamLeads: is("admin") || is("manager"),

    // Inventory permissions
    canCreateInventory: is("admin") || is("manager"),
    canEditInventory: is("admin"),
    canDeleteInventory: is("admin"),

    // User management
    canManageUsers: is("admin"),
    canManageTeams: is("admin"),
    canManageSettings: is("admin"),

    // Reports
    canViewAllReports: is("admin"),
    canViewTeamReports: is("admin") || is("manager"),
    canViewMarketingROI: is("admin"),
  };
}
