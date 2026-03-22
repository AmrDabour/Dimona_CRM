import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { useDashboard, useConversionFunnel } from "@/services/reportService";
import { useLeaderboard } from "@/services/gamificationService";
import { StatCard } from "@/components/shared/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Users,
  UserPlus,
  Activity,
  Clock,
  AlertCircle,
  Trophy,
  Star,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  FunnelChart,
  Funnel,
  LabelList,
  Cell,
} from "recharts";

const CHART_COLORS = [
  "hsl(221, 83%, 53%)",
  "hsl(262, 83%, 58%)",
  "hsl(330, 81%, 60%)",
  "hsl(24, 94%, 50%)",
  "hsl(142, 71%, 45%)",
  "hsl(47, 96%, 53%)",
  "hsl(199, 89%, 48%)",
];

const FUNNEL_COLORS = [
  "hsl(221, 83%, 53%)",
  "hsl(199, 89%, 48%)",
  "hsl(142, 71%, 45%)",
  "hsl(47, 96%, 53%)",
  "hsl(24, 94%, 50%)",
  "hsl(330, 81%, 60%)",
];

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-[120px] rounded-xl" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-[380px] rounded-xl" />
        <Skeleton className="h-[380px] rounded-xl" />
      </div>
    </div>
  );
}

const TIER_STYLES: Record<string, string> = {
  gold: "text-amber-600 dark:text-amber-400",
  silver: "text-slate-500 dark:text-slate-300",
  bronze: "text-orange-600 dark:text-orange-400",
};

export default function DashboardPage() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const { data: dashboard, isLoading: dashLoading } = useDashboard();
  const { data: funnel, isLoading: funnelLoading } = useConversionFunnel();
  const { data: leaderboard } = useLeaderboard(undefined, undefined, 5);

  if (dashLoading || funnelLoading) {
    return (
      <div className="p-6">
        <DashboardSkeleton />
      </div>
    );
  }

  const pipelineData = dashboard
    ? Object.entries(dashboard.pipeline).map(([stage, count]) => ({
        stage: t(`pipeline.${stage}`, stage),
        count,
      }))
    : [];

  const funnelData = funnel
    ? funnel.funnel.map((s) => ({
        name: t(`pipeline.${s.stage}`, s.stage),
        value: s.count,
        dropOff: s.drop_off_rate,
      }))
    : [];

  return (
    <div className="space-y-6 p-6">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {t("dashboard.welcome", { name: user?.full_name })}
        </h1>
        <p className="text-muted-foreground">{t("dashboard.subtitle")}</p>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <StatCard
          title={t("dashboard.newToday")}
          value={dashboard?.leads.new_today ?? 0}
          icon={Users}
        />
        <StatCard
          title={t("dashboard.newThisWeek")}
          value={dashboard?.leads.new_this_week ?? 0}
          icon={UserPlus}
          trend={
            dashboard && dashboard.leads.new_this_week > 0
              ? { direction: "up", value: `${dashboard.leads.new_this_week}` }
              : undefined
          }
        />
        <StatCard
          title={t("dashboard.totalActive")}
          value={dashboard?.leads.total_active ?? 0}
          icon={Activity}
        />
        <StatCard
          title={t("dashboard.pendingActivities")}
          value={dashboard?.activities.pending ?? 0}
          icon={Clock}
        />
        <StatCard
          title={t("dashboard.overdueActivities")}
          value={dashboard?.activities.overdue ?? 0}
          icon={AlertCircle}
          trend={
            dashboard && dashboard.activities.overdue > 0
              ? { direction: "down", value: `${dashboard.activities.overdue}` }
              : undefined
          }
        />
        <StatCard
          title={t("gamification.myPoints")}
          value={dashboard?.gamification?.total_points ?? 0}
          icon={Trophy}
          description={
            dashboard?.gamification?.tier
              ? `${t(`gamification.${dashboard.gamification.tier.name}`)} · #${dashboard.gamification.rank || "-"}`
              : undefined
          }
        />
      </div>

      {/* Charts row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Pipeline bar chart */}
        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard.pipelineOverview")}</CardTitle>
          </CardHeader>
          <CardContent>
            {pipelineData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={pipelineData}
                  margin={{ top: 8, right: 8, bottom: 0, left: -12 }}
                >
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="stage"
                    tick={{ fontSize: 12 }}
                    className="fill-muted-foreground"
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fontSize: 12 }}
                    className="fill-muted-foreground"
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: "0.5rem",
                      border: "1px solid hsl(var(--border))",
                      background: "hsl(var(--popover))",
                      color: "hsl(var(--popover-foreground))",
                    }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {pipelineData.map((_, idx) => (
                      <Cell
                        key={idx}
                        fill={CHART_COLORS[idx % CHART_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="py-12 text-center text-sm text-muted-foreground">
                {t("common.noData")}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Conversion funnel */}
        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard.conversionFunnel")}</CardTitle>
          </CardHeader>
          <CardContent>
            {funnelData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <FunnelChart>
                  <Tooltip
                    contentStyle={{
                      borderRadius: "0.5rem",
                      border: "1px solid hsl(var(--border))",
                      background: "hsl(var(--popover))",
                      color: "hsl(var(--popover-foreground))",
                    }}
                  />
                  <Funnel dataKey="value" data={funnelData} isAnimationActive>
                    <LabelList
                      dataKey="name"
                      position="right"
                      className="fill-foreground text-xs"
                    />
                    <LabelList
                      dataKey="value"
                      position="center"
                      className="fill-white text-sm font-semibold"
                    />
                    {funnelData.map((_, idx) => (
                      <Cell
                        key={idx}
                        fill={FUNNEL_COLORS[idx % FUNNEL_COLORS.length]}
                      />
                    ))}
                  </Funnel>
                </FunnelChart>
              </ResponsiveContainer>
            ) : (
              <p className="py-12 text-center text-sm text-muted-foreground">
                {t("common.noData")}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Funnel summary */}
      {funnel && (
        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard.funnelSummary")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">
                  {t("dashboard.totalLeads")}
                </p>
                <p className="text-xl font-bold">{funnel.summary.total_leads}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">
                  {t("dashboard.totalWon")}
                </p>
                <p className="text-xl font-bold text-emerald-600">
                  {funnel.summary.total_won}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">
                  {t("dashboard.totalLost")}
                </p>
                <p className="text-xl font-bold text-red-600">
                  {funnel.summary.total_lost}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">
                  {t("dashboard.conversionRate")}
                </p>
                <p className="text-xl font-bold">
                  {funnel.summary.overall_conversion.toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Mini leaderboard -- Top 5 */}
      {leaderboard && leaderboard.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-amber-500" />
              {t("gamification.topPerformers")}
            </CardTitle>
            <Link
              to="/leaderboard"
              className="text-sm font-medium text-primary hover:underline"
            >
              {t("gamification.viewAll")}
            </Link>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {leaderboard.map((entry) => {
                const isCurrent = entry.user_id === user?.id;
                return (
                  <div
                    key={entry.user_id}
                    className={cn(
                      "flex items-center gap-3 py-2.5",
                      isCurrent && "rounded bg-primary/5 px-2",
                    )}
                  >
                    <span className="w-6 text-center font-bold text-muted-foreground">
                      {entry.rank}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {entry.full_name}
                      </p>
                    </div>
                    <span
                      className={cn(
                        "flex items-center gap-1 text-xs font-semibold capitalize",
                        TIER_STYLES[entry.tier.name] ?? TIER_STYLES.bronze,
                      )}
                    >
                      <Star className="h-3 w-3" />
                      {t(`gamification.${entry.tier.name}`, entry.tier.name)}
                    </span>
                    <span className="w-12 text-end font-bold">
                      {entry.total_points}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
