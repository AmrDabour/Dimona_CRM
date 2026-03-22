import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  LayoutDashboard,
  Users,
  Kanban,
  Building2,
  CalendarCheck,
  BarChart3,
  Shield,
  ChevronDown,
  Building,
  Trophy,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/uiStore";
import { usePermissions } from "@/hooks/usePermissions";

interface NavItem {
  to: string;
  label: string;
  icon?: LucideIcon;
  roles?: string[];
}

interface NavSection {
  key: string;
  label: string;
  icon: LucideIcon;
  items: NavItem[];
  roles?: string[];
}

const linkBase =
  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground";
const linkActive = "bg-sidebar-accent text-sidebar-accent-foreground";

export function Sidebar() {
  const { t } = useTranslation();
  const sidebarOpen = useUIStore((s) => s.sidebarOpen);
  const { isAdmin, isManager, role } = usePermissions();
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({});

  const toggleSection = (key: string) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const topNav: NavItem[] = [
    { to: "/", label: t("nav.dashboard"), icon: LayoutDashboard },
    { to: "/leads", label: t("nav.leads"), icon: Users },
    { to: "/pipeline", label: t("nav.pipeline"), icon: Kanban },
    { to: "/leaderboard", label: t("nav.leaderboard"), icon: Trophy },
  ];

  const sections: NavSection[] = [
    {
      key: "inventory",
      label: t("nav.inventory"),
      icon: Building2,
      items: [
        { to: "/inventory/developers", label: t("nav.developers") },
        { to: "/inventory/projects", label: t("nav.projects") },
        { to: "/inventory/units", label: t("nav.units") },
      ],
    },
    {
      key: "activities",
      label: t("nav.activities"),
      icon: CalendarCheck,
      items: [{ to: "/activities", label: t("nav.activities") }],
    },
    {
      key: "reports",
      label: t("nav.reports"),
      icon: BarChart3,
      items: [
        { to: "/reports", label: t("nav.overview") },
        {
          to: "/reports/agent-performance",
          label: t("nav.agentPerformance"),
          roles: ["admin", "manager"],
        },
        {
          to: "/reports/marketing-roi",
          label: t("nav.marketingRoi"),
          roles: ["admin"],
        },
      ],
    },
    {
      key: "admin",
      label: t("nav.admin"),
      icon: Shield,
      roles: ["admin"],
      items: [
        { to: "/admin/users", label: t("nav.users") },
        { to: "/admin/teams", label: t("nav.teams") },
        { to: "/admin/gamification", label: t("nav.gamification") },
        { to: "/admin/settings", label: t("nav.settings") },
      ],
    },
  ];

  const hasAccess = (roles?: string[]) => {
    if (!roles) return true;
    return role ? roles.includes(role) : false;
  };

  const renderLink = (item: NavItem, collapsed: boolean) => {
    if (!hasAccess(item.roles)) return null;
    const Icon = item.icon;

    return (
      <NavLink
        key={item.to}
        to={item.to}
        end={item.to === "/"}
        className={({ isActive }) => cn(linkBase, isActive && linkActive)}
        title={collapsed ? item.label : undefined}
      >
        {Icon && <Icon className="h-5 w-5 shrink-0" />}
        {!collapsed && <span className="truncate">{item.label}</span>}
      </NavLink>
    );
  };

  const renderSection = (section: NavSection, collapsed: boolean) => {
    if (!hasAccess(section.roles)) return null;

    const visibleItems = section.items.filter((i) => hasAccess(i.roles));
    if (visibleItems.length === 0) return null;

    if (section.key === "activities") {
      return (
        <NavLink
          key={section.key}
          to="/activities"
          className={({ isActive }) => cn(linkBase, isActive && linkActive)}
          title={collapsed ? section.label : undefined}
        >
          <section.icon className="h-5 w-5 shrink-0" />
          {!collapsed && (
            <span className="truncate">{section.label}</span>
          )}
        </NavLink>
      );
    }

    const isOpen = openSections[section.key] ?? false;

    if (collapsed) {
      return (
        <div key={section.key} className="relative group">
          <button
            className={cn(linkBase, "w-full justify-center px-0")}
            title={section.label}
          >
            <section.icon className="h-5 w-5 shrink-0" />
          </button>
          <div className="absolute start-full top-0 z-50 ms-1 hidden min-w-[10rem] rounded-md border bg-popover p-1 shadow-md group-hover:block">
            <p className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
              {section.label}
            </p>
            {visibleItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "block rounded-sm px-2 py-1.5 text-sm transition-colors hover:bg-accent",
                    isActive && "bg-accent font-medium"
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </div>
      );
    }

    return (
      <div key={section.key}>
        <button
          onClick={() => toggleSection(section.key)}
          className={cn(linkBase, "w-full justify-between")}
        >
          <span className="flex items-center gap-3">
            <section.icon className="h-5 w-5 shrink-0" />
            <span className="truncate">{section.label}</span>
          </span>
          <ChevronDown
            className={cn(
              "h-4 w-4 shrink-0 transition-transform",
              isOpen && "rotate-180"
            )}
          />
        </button>
        {isOpen && (
          <div className="ms-4 mt-1 flex flex-col gap-0.5 border-s ps-3">
            {visibleItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/reports"}
                className={({ isActive }) =>
                  cn(
                    "rounded-md px-3 py-1.5 text-sm transition-colors hover:bg-sidebar-accent",
                    isActive &&
                      "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <aside
      className={cn(
        "flex h-full flex-col border-e bg-sidebar-background text-sidebar-foreground transition-[width] duration-200",
        sidebarOpen ? "w-64" : "w-16"
      )}
    >
      {/* Brand */}
      <div
        className={cn(
          "flex h-14 items-center border-b px-4 gap-3",
          !sidebarOpen && "justify-center px-0"
        )}
      >
        <Building className="h-6 w-6 shrink-0 text-sidebar-primary" />
        {sidebarOpen && (
          <span className="text-lg font-bold tracking-tight text-sidebar-primary">
            Dimora
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {topNav.map((item) => renderLink(item, !sidebarOpen))}

        <div className="my-2 h-px bg-sidebar-border" />

        {sections.map((section) => renderSection(section, !sidebarOpen))}
      </nav>

      {/* Footer */}
      {sidebarOpen && (
        <div className="border-t p-4">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} Dimora CRM
          </p>
        </div>
      )}
    </aside>
  );
}
