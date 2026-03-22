import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import {
  useAgentPerformance,
  useMyPerformance,
} from "@/services/reportService";
import { useUsers } from "@/services/userService";
import { usePermissions } from "@/hooks/usePermissions";
import { StatCard } from "@/components/shared/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Users,
  Trophy,
  XCircle,
  TrendingUp,
  Target,
  Phone,
  Calendar,
  BarChart3,
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

function PerformanceSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-[120px] rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-[380px] rounded-xl" />
    </div>
  );
}

export default function AgentPerformancePage() {
  const { t } = useTranslation();
  const { id: paramId } = useParams<{ id: string }>();
  const { isAdmin } = usePermissions();
  const [selectedAgentId, setSelectedAgentId] = useState(paramId ?? "");

  const agentId = selectedAgentId || paramId || "";
  const useOwnPerformance = !agentId;

  const { data: agentPerformance, isLoading: agentLoading } =
    useAgentPerformance(agentId);
  const { data: myPerformance, isLoading: myLoading } = useMyPerformance();
  const { data: users } = useUsers();

  const performance = useOwnPerformance ? myPerformance : agentPerformance;
  const isLoading = useOwnPerformance ? myLoading : agentLoading;

  if (isLoading) {
    return (
      <div className="p-6">
        <PerformanceSkeleton />
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
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {performance?.agent.name
              ? t("reports.agentPerformanceFor", {
                  name: performance.agent.name,
                  defaultValue: `${performance.agent.name} — Performance`,
                })
              : t("reports.myPerformance", "My Performance")}
          </h1>
          {performance?.period && (
            <p className="text-muted-foreground">
              {performance.period.start} — {performance.period.end}
            </p>
          )}
        </div>

        {isAdmin && users && (
          <Select value={selectedAgentId} onValueChange={setSelectedAgentId}>
            <SelectTrigger className="w-[240px]">
              <SelectValue
                placeholder={t("reports.selectAgent", "Select an agent")}
              />
            </SelectTrigger>
            <SelectContent>
              {users.map((u) => (
                <SelectItem key={u.id} value={u.id}>
                  {u.full_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard
          title={t("reports.totalLeads", "Total Leads")}
          value={performance?.leads.total ?? 0}
          icon={Users}
        />
        <StatCard
          title={t("reports.wonDeals", "Won")}
          value={performance?.leads.won ?? 0}
          icon={Trophy}
        />
        <StatCard
          title={t("reports.lostDeals", "Lost")}
          value={performance?.leads.lost ?? 0}
          icon={XCircle}
        />
        <StatCard
          title={t("reports.conversionRate", "Conversion Rate")}
          value={`${(performance?.metrics.conversion_rate ?? 0).toFixed(1)}%`}
          icon={TrendingUp}
        />
        <StatCard
          title={t("reports.winRate", "Win Rate")}
          value={`${(performance?.metrics.win_rate ?? 0).toFixed(1)}%`}
          icon={Target}
        />
      </div>

      {/* Pipeline chart */}
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

      {/* Activity stats */}
      <Card>
        <CardHeader>
          <CardTitle>
            {t("reports.activityStats", "Activity Statistics")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="flex items-center gap-3 rounded-lg border p-4">
              <div className="rounded-lg bg-blue-500/10 p-2">
                <Phone className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {performance?.activities.calls ?? 0}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t("reports.calls", "Calls")}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg border p-4">
              <div className="rounded-lg bg-violet-500/10 p-2">
                <Calendar className="h-5 w-5 text-violet-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {performance?.activities.meetings ?? 0}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t("reports.meetings", "Meetings")}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg border p-4">
              <div className="rounded-lg bg-emerald-500/10 p-2">
                <BarChart3 className="h-5 w-5 text-emerald-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {performance?.activities.total ?? 0}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t("reports.totalActivities", "Total")}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
