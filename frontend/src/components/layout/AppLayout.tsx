import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Toaster } from "@/components/ui/sonner";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { useUIStore } from "@/stores/uiStore";
import { useMediaQuery } from "@/hooks/useMediaQuery";

export function AppLayout() {
  const { t } = useTranslation();
  const isDesktop = useMediaQuery("(min-width: 768px)");
  const sidebarOpen = useUIStore((s) => s.sidebarOpen);
  const setSidebarOpen = useUIStore((s) => s.setSidebarOpen);

  const mobileDrawerOpen = !isDesktop && sidebarOpen;

  useEffect(() => {
    if (mobileDrawerOpen) {
      const prev = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = prev;
      };
    }
  }, [mobileDrawerOpen]);

  return (
    <div className="flex h-[100dvh] min-h-0 w-full overflow-hidden bg-background">
      {!isDesktop && mobileDrawerOpen && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/50 backdrop-blur-[2px] md:hidden"
          aria-label={t("common.closeMenu")}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="min-h-0 flex-1 overflow-x-hidden overflow-y-auto px-3 py-4 sm:px-4 sm:py-5 md:p-6">
          <Outlet />
        </main>
      </div>

      <Toaster />
    </div>
  );
}
