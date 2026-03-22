import { useTranslation } from "react-i18next";
import { useMyPerformance } from "@/services/reportService";
import { usePermissions } from "@/hooks/usePermissions";
import { StatCard } from "@/components/shared/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Link } from "react-router-dom";
import {
  Users,
  Trophy,
  XCircle,
  TrendingUp,
  Phone,
  Calendar,
  BarChart3,
  UsersRound,
  Megaphone,
  ArrowRight,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
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

function ReportsSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-[120px] rounded-xl" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-[380px] rounded-xl" />
        <Skeleton className="h-[260px] rounded-xl" />
      </div>
    </div>
  );
}

export default function ReportsPage() {
  const { t } = useTranslation();
  const { canViewAllReports, canViewTeamReports, canViewMarketingROI } =
    usePermissions();
  const { data: performance, isLoading } = useMyPerformance();

  if (isLoading) {
    return (
      <div className="p-6">
        <ReportsSkeleton />
      </div>
    );
  }

  const pipelineData = performance
    ? Object.entries(performance.leads.pipeline_breakdown).map(
        ([stage, count]) => ({
          stage: t(`pipeline.${stage}`, stage),
          count,
        })
      )
    : [];

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {t("reports.title", "Reports")}
        </h1>
        <p className="text-muted-foreground">
          {t("reports.subtitle", "Track your performance and team metrics")}
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title={t("reports.totalLeads", "Total Leads")}
          value={performance?.leads.total ?? 0}
          icon={Users}
        />
        <StatCard
          title={t("reports.wonDeals", "Won Deals")}
          value={performance?.leads.won ?? 0}
          icon={Trophy}
        />
        <StatCard
          title={t("reports.lostDeals", "Lost Deals")}
          value={performance?.leads.lost ?? 0}
          icon={XCircle}
        />
        <StatCard
          title={t("reports.conversionRate", "Conversion Rate")}
          value={`${(performance?.metrics.conversion_rate ?? 0).toFixed(1)}%`}
          icon={TrendingUp}
        />
      </div>

      {/* Charts row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Pipeline breakdown chart */}
        <Card>
          <CardHeader>
            <CardTitle>
              {t("reports.pipelineBreakdown", "Pipeline Breakdown")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {pipelineData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={pipelineData}
                  margin={{ top: 8, right: 8, bottom: 0, left: -12 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    className="stroke-muted"
                  />
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

        {/* Activity breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>
              {t("reports.activityBreakdown", "Activity Breakdown")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-blue-500/10 p-2">
                    <Phone className="h-5 w-5 text-blue-500" />
                  </div>
                  <div>
                    <p className="font-medium">
                      {t("reports.calls", "Calls")}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {t("reports.totalCalls", "Total calls made")}
                    </p>
                  </div>
                </div>
                <p className="text-2xl font-bold">
                  {performance?.activities.calls ?? 0}
                </p>
              </div>
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-violet-500/10 p-2">
                    <Calendar className="h-5 w-5 text-violet-500" />
                  </div>
                  <div>
                    <p className="font-medium">
                      {t("reports.meetings", "Meetings")}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {t("reports.totalMeetings", "Total meetings held")}
                    </p>
                  </div>
                </div>
                <p className="text-2xl font-bold">
                  {performance?.activities.meetings ?? 0}
                </p>
              </div>
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-emerald-500/10 p-2">
                    <BarChart3 className="h-5 w-5 text-emerald-500" />
                  </div>
                  <div>
                    <p className="font-medium">
                      {t("reports.totalActivities", "Total Activities")}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {t("reports.allActivities", "All activity types")}
                    </p>
                  </div>
                </div>
                <p className="text-2xl font-bold">
                  {performance?.activities.total ?? 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Admin / Manager report links */}
      {(canViewAllReports || canViewTeamReports) && (
        <div>
          <h2 className="mb-4 text-lg font-semibold">
            {t("reports.moreReports", "More Reports")}
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Link to="/reports/agent-performance" className="group">
              <Card className="transition-shadow group-hover:shadow-md">
                <CardContent className="flex items-center gap-4 p-6">
                  <div className="rounded-lg bg-blue-500/10 p-3">
                    <Users className="h-6 w-6 text-blue-500" />
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold">
                      {t("reports.agentPerformance", "Agent Performance")}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {t(
                        "reports.agentPerformanceDesc",
                        "View individual agent metrics"
                      )}
                    </p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
                </CardContent>
              </Card>
            </Link>

            {canViewTeamReports && (
              <Link to="/reports/team-performance" className="group">
                <Card className="transition-shadow group-hover:shadow-md">
                  <CardContent className="flex items-center gap-4 p-6">
                    <div className="rounded-lg bg-violet-500/10 p-3">
                      <UsersRound className="h-6 w-6 text-violet-500" />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold">
                        {t("reports.teamPerformance", "Team Performance")}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {t(
                          "reports.teamPerformanceDesc",
                          "View team-level metrics"
                        )}
                      </p>
                    </div>
                    <ArrowRight className="h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
                  </CardContent>
                </Card>
              </Link>
            )}

            {canViewMarketingROI && (
              <Link to="/reports/marketing-roi" className="group">
                <Card className="transition-shadow group-hover:shadow-md">
                  <CardContent className="flex items-center gap-4 p-6">
                    <div className="rounded-lg bg-amber-500/10 p-3">
                      <Megaphone className="h-6 w-6 text-amber-500" />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold">
                        {t("reports.marketingROI", "Marketing ROI")}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {t(
                          "reports.marketingROIDesc",
                          "Campaign costs & lead source analysis"
                        )}
                      </p>
                    </div>
                    <ArrowRight className="h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
                  </CardContent>
                </Card>
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
