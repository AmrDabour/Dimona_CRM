import { Routes, Route, Navigate } from "react-router-dom";
import { Suspense, lazy, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { AppLayout } from "@/components/layout/AppLayout";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { useUIStore } from "@/stores/uiStore";

const LoginPage = lazy(() => import("@/pages/LoginPage"));
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const LeadsPage = lazy(() => import("@/pages/leads/LeadsPage"));
const LeadDetailPage = lazy(() => import("@/pages/leads/LeadDetailPage"));
const PipelinePage = lazy(() => import("@/pages/PipelinePage"));
const DevelopersPage = lazy(() => import("@/pages/inventory/DevelopersPage"));
const ProjectsPage = lazy(() => import("@/pages/inventory/ProjectsPage"));
const UnitsPage = lazy(() => import("@/pages/inventory/UnitsPage"));
const ActivitiesPage = lazy(() => import("@/pages/ActivitiesPage"));
const ReportsPage = lazy(() => import("@/pages/reports/ReportsPage"));
const AgentPerformancePage = lazy(() => import("@/pages/reports/AgentPerformancePage"));
const MarketingROIPage = lazy(() => import("@/pages/reports/MarketingROIPage"));
const LeaderboardPage = lazy(() => import("@/pages/LeaderboardPage"));
const UsersPage = lazy(() => import("@/pages/admin/UsersPage"));
const TeamsPage = lazy(() => import("@/pages/admin/TeamsPage"));
const SettingsPage = lazy(() => import("@/pages/admin/SettingsPage"));
const GamificationSettingsPage = lazy(() => import("@/pages/admin/GamificationSettingsPage"));

function LoadingFallback() {
  const { t } = useTranslation();
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-muted-foreground">{t("common.loading")}</div>
    </div>
  );
}

export default function App() {
  const theme = useUIStore((s) => s.theme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="leads" element={<LeadsPage />} />
          <Route path="leads/:id" element={<LeadDetailPage />} />
          <Route path="pipeline" element={<PipelinePage />} />
          <Route path="inventory/developers" element={<DevelopersPage />} />
          <Route path="inventory/projects" element={<ProjectsPage />} />
          <Route path="inventory/units" element={<UnitsPage />} />
          <Route path="activities" element={<ActivitiesPage />} />
          <Route path="leaderboard" element={<LeaderboardPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="reports/agent-performance" element={<AgentPerformancePage />} />
          <Route path="reports/agent/:id" element={<AgentPerformancePage />} />
          <Route path="reports/marketing-roi" element={<MarketingROIPage />} />
          <Route
            path="admin/users"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <UsersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="admin/teams"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <TeamsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="admin/settings"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="admin/gamification"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <GamificationSettingsPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
