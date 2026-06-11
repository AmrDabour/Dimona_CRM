import { useAuthStore, type UserRole } from "@/stores/authStore";

export function usePermissions() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role;

  const is = (r: UserRole) => role === r;

  return {
    role,
    isAdmin: is("admin"),
    isBranchManager: is("branch_manager"),
    isManager: is("sales_manager"),
    isAgent: is("sales_rep"),

    // Lead permissions
    canCreateLead: true,
    canDeleteLead: is("admin"),
    canExportLeads: is("admin") || is("branch_manager"),
    canImportLeads: is("admin") || is("branch_manager") || is("sales_manager"),
    canAssignLead: is("admin") || is("branch_manager") || is("sales_manager"),
    canReadAllLeads: is("admin"),
    canReadTeamLeads: is("admin") || is("branch_manager") || is("sales_manager"),

    // Inventory permissions
    canCreateInventory: is("admin") || is("branch_manager") || is("sales_manager"),
    canEditInventory: is("admin"),
    canDeleteInventory: is("admin"),

    // User management
    canManageUsers: is("admin"),
    canManageTeams: is("admin"),
    canManageSettings: is("admin"),

    // Reports
    canViewAllReports: is("admin") || is("branch_manager"),
    canViewTeamReports: is("admin") || is("branch_manager") || is("sales_manager"),
    canViewMarketingROI: is("admin"),
    canViewTeamTasks: is("admin") || is("branch_manager") || is("sales_manager"),
  };
}
