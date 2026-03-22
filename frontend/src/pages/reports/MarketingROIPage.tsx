import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useMarketingROI } from "@/services/reportService";
import { StatCard } from "@/components/shared/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { DataTable } from "@/components/shared/DataTable";
import { formatCurrency } from "@/lib/utils";
import type { ColumnDef } from "@tanstack/react-table";
import type { SourceROI } from "@/types/report";
import {
  DollarSign,
  Users,
  Trophy,
  TrendingUp,
  Target,
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
  Legend,
} from "recharts";

function ROISkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-[120px] rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-[380px] rounded-xl" />
      <Skeleton className="h-[300px] rounded-xl" />
    </div>
  );
}

export default function MarketingROIPage() {
  const { t } = useTranslation();
  const { data: roi, isLoading } = useMarketingROI();

  const columns = useMemo<ColumnDef<SourceROI>[]>(
    () => [
      {
        accessorKey: "source_name",
        header: t("reports.sourceName", "Source"),
      },
      {
        accessorKey: "campaign_name",
        header: t("reports.campaign", "Campaign"),
        cell: ({ row }) => row.original.campaign_name || "—",
      },
      {
        accessorKey: "campaign_cost",
        header: t("reports.cost", "Cost"),
        cell: ({ row }) => formatCurrency(row.original.campaign_cost),
      },
      {
        accessorKey: "total_leads",
        header: t("reports.leads", "Leads"),
      },
      {
        accessorKey: "won_leads",
        header: t("reports.won", "Won"),
        cell: ({ row }) => (
          <span className="font-medium text-emerald-600">
            {row.original.won_leads}
          </span>
        ),
      },
      {
        accessorKey: "lost_leads",
        header: t("reports.lost", "Lost"),
        cell: ({ row }) => (
          <span className="font-medium text-red-600">
            {row.original.lost_leads}
          </span>
        ),
      },
      {
        accessorKey: "cost_per_lead",
        header: t("reports.costPerLead", "Cost/Lead"),
        cell: ({ row }) => formatCurrency(row.original.cost_per_lead),
      },
      {
        accessorKey: "cost_per_won",
        header: t("reports.costPerWon", "Cost/Won"),
        cell: ({ row }) => formatCurrency(row.original.cost_per_won),
      },
      {
        accessorKey: "conversion_rate",
        header: t("reports.conversion", "Conv. %"),
        cell: ({ row }) => `${row.original.conversion_rate.toFixed(1)}%`,
      },
    ],
    [t]
  );

  const chartData = roi?.sources.map((s) => ({
    name: s.source_name,
    leads: s.total_leads,
    cost: s.campaign_cost,
  }));

  if (isLoading) {
    return (
      <div className="p-6">
        <ROISkeleton />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {t("reports.marketingROI", "Marketing ROI")}
        </h1>
        <p className="text-muted-foreground">
          {t(
            "reports.marketingROISubtitle",
            "Analyze campaign costs and lead source effectiveness"
          )}
        </p>
      </div>

      {/* Summary stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <StatCard
          title={t("reports.totalCampaignCost", "Total Campaign Cost")}
          value={formatCurrency(roi?.summary.total_campaign_cost ?? 0)}
          icon={DollarSign}
        />
        <StatCard
          title={t("reports.totalLeads", "Total Leads")}
          value={roi?.summary.total_leads ?? 0}
          icon={Users}
        />
        <StatCard
          title={t("reports.totalWon", "Total Won")}
          value={roi?.summary.total_won ?? 0}
          icon={Trophy}
        />
        <StatCard
          title={t("reports.avgCostPerLead", "Avg Cost/Lead")}
          value={formatCurrency(roi?.summary.avg_cost_per_lead ?? 0)}
          icon={Target}
        />
        <StatCard
          title={t("reports.avgCostPerWon", "Avg Cost/Won")}
          value={formatCurrency(roi?.summary.avg_cost_per_won ?? 0)}
          icon={BarChart3}
        />
        <StatCard
          title={t("reports.overallConversion", "Overall Conversion")}
          value={`${(roi?.summary.overall_conversion ?? 0).toFixed(1)}%`}
          icon={TrendingUp}
        />
      </div>

      {/* Source comparison chart */}
      {chartData && chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>
              {t("reports.sourceComparison", "Source Comparison")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={chartData}
                margin={{ top: 8, right: 8, bottom: 0, left: -12 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  className="stroke-muted"
                />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 12 }}
                  className="fill-muted-foreground"
                />
                <YAxis
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
                <Legend />
                <Bar
                  dataKey="leads"
                  name={t("reports.leads", "Leads")}
                  fill="hsl(221, 83%, 53%)"
                  radius={[6, 6, 0, 0]}
                />
                <Bar
                  dataKey="cost"
                  name={t("reports.cost", "Cost")}
                  fill="hsl(24, 94%, 50%)"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Source detail table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {t("reports.sourceDetails", "Source Details")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            data={roi?.sources ?? []}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>
    </div>
  );
}
