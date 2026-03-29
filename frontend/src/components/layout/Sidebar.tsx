import { useState, useEffect, useRef, useCallback } from "react";
import { NavLink, useLocation } from "react-router-dom";
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
import { useMediaQuery } from "@/hooks/useMediaQuery";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

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

/** Flyout for collapsed desktop sidebar: hover + delayed close; click for touch. */
function CollapsedSectionFlyout({
  section,
  items,
  isRtl,
  onNavigate,
}: {
  section: NavSection;
  items: NavItem[];
  isRtl: boolean;
  onNavigate: () => void;
}) {
  const [open, setOpen] = useState(false);
  const closeTimer = useRef<number | null>(null);

  const cancelClose = useCallback(() => {
    if (closeTimer.current) {
      clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
  }, []);

  const scheduleClose = useCallback(() => {
    cancelClose();
    closeTimer.current = window.setTimeout(() => setOpen(false), 200);
  }, [cancelClose]);

  const openNow = useCallback(() => {
    cancelClose();
    setOpen(true);
  }, [cancelClose]);

  useEffect(() => () => cancelClose(), [cancelClose]);

  return (
    <Popover open={open} onOpenChange={setOpen} modal={false}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            linkBase,
            "w-full justify-center px-0",
            open && "bg-sidebar-accent text-sidebar-accent-foreground"
          )}
          aria-expanded={open}
          aria-haspopup="true"
          title={section.label}
          onMouseEnter={openNow}
          onMouseLeave={scheduleClose}
        >
          <section.icon className="h-5 w-5 shrink-0" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        side={isRtl ? "left" : "right"}
        align="start"
        sideOffset={10}
        collisionPadding={16}
        className="w-[min(calc(100vw-2rem),15rem)] rounded-xl border bg-popover p-0 py-1.5 shadow-lg ring-1 ring-border/60"
        onMouseEnter={openNow}
        onMouseLeave={scheduleClose}
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <p className="border-b border-border/70 px-3 pb-2 pt-1 text-[0.65rem] font-semibold uppercase tracking-wider text-muted-foreground">
          {section.label}
        </p>
        <nav className="flex flex-col gap-0.5 px-1.5 pt-1" role="menu">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/reports"}
              role="menuitem"
              onClick={() => {
                setOpen(false);
                onNavigate();
              }}
              className={({ isActive }) =>
                cn(
                  "rounded-md px-2.5 py-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground",
                  isActive && "bg-accent font-medium text-accent-foreground"
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </PopoverContent>
    </Popover>
  );
}

export function Sidebar() {
  const { t, i18n } = useTranslation();
  const isRtl = i18n.dir() === "rtl";
  const location = useLocation();
  const isDesktop = useMediaQuery("(min-width: 768px)");
  const sidebarOpen = useUIStore((s) => s.sidebarOpen);
  const setSidebarOpen = useUIStore((s) => s.setSidebarOpen);
  const { role } = usePermissions();
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({});

  const prevDesktopRef = useRef<boolean | null>(null);
  useEffect(() => {
    if (prevDesktopRef.current === true && !isDesktop) setSidebarOpen(false);
    prevDesktopRef.current = isDesktop;
  }, [isDesktop, setSidebarOpen]);

  useEffect(() => {
    if (!isDesktop) setSidebarOpen(false);
  }, [location.pathname, isDesktop, setSidebarOpen]);

  const closeMobileNav = () => {
    if (!isDesktop) setSidebarOpen(false);
  };

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
        {
          to: "/team/tasks",
          label: t("nav.teamTasks"),
          roles: ["admin", "manager"],
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

  const narrowNav = isDesktop && !sidebarOpen;
  const mobileHidden = !isDesktop && !sidebarOpen;

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
        onClick={closeMobileNav}
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
          onClick={closeMobileNav}
        >
          <section.icon className="h-5 w-5 shrink-0" />
          {!collapsed && <span className="truncate">{section.label}</span>}
        </NavLink>
      );
    }

    const isOpen = openSections[section.key] ?? false;

    if (collapsed) {
      return (
        <CollapsedSectionFlyout
          key={section.key}
          section={section}
          items={visibleItems}
          isRtl={isRtl}
          onNavigate={closeMobileNav}
        />
      );
    }

    return (
      <div key={section.key}>
        <button
          type="button"
          onClick={() => toggleSection(section.key)}
          className={cn(linkBase, "w-full justify-between")}
        >
          <span className="flex min-w-0 items-center gap-3">
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
                onClick={closeMobileNav}
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
        "flex flex-col border-e bg-sidebar-background text-sidebar-foreground",
        "transition-[width,transform] duration-200 ease-out",
        isDesktop
          ? cn(
              "relative h-full shrink-0",
              sidebarOpen ? "w-64" : "w-16"
            )
          : cn(
              "fixed inset-y-0 z-40 w-[min(18rem,calc(100vw-1rem))] max-w-[85vw] shadow-2xl",
              isRtl ? "end-0" : "start-0",
              mobileHidden &&
                (isRtl ? "translate-x-full" : "-translate-x-full"),
              mobileHidden && "pointer-events-none"
            )
      )}
      aria-hidden={mobileHidden}
    >
      <div
        className={cn(
          "flex h-14 shrink-0 items-center gap-3 border-b px-4",
          narrowNav && "justify-center px-0"
        )}
      >
        <Building className="h-6 w-6 shrink-0 text-sidebar-primary" />
        {!narrowNav && (
          <span className="text-lg font-bold tracking-tight text-sidebar-primary">
            Dimora
          </span>
        )}
      </div>

      <nav
        className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto overflow-x-hidden p-3 overscroll-contain"
        aria-label={t("nav.mainNavigation")}
      >
        {topNav.map((item) => renderLink(item, narrowNav))}

        <div className="my-2 h-px shrink-0 bg-sidebar-border" />

        {sections.map((section) => renderSection(section, narrowNav))}
      </nav>

      {!narrowNav && (
        <div className="shrink-0 border-t p-4">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} Dimora CRM
          </p>
        </div>
      )}
    </aside>
  );
}
