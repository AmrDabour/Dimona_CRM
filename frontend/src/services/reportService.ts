import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  DashboardSummary,
  AgentPerformanceReport,
  TeamPerformanceReport,
  MarketingROIReport,
  ConversionFunnelReport,
} from "@/types/report";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardSummary>("/reports/dashboard").then((r) => r.data),
  });
}

export function useAgentPerformance(agentId: string) {
  return useQuery({
    queryKey: ["reports", "agent", agentId],
    queryFn: () =>
      api.get<AgentPerformanceReport>(`/reports/agent-performance/${agentId}`).then((r) => r.data),
    enabled: !!agentId,
  });
}

export function useMyPerformance() {
  return useQuery({
    queryKey: ["reports", "my-performance"],
    queryFn: () => api.get<AgentPerformanceReport>("/reports/my-performance").then((r) => r.data),
  });
}

export function useTeamPerformance(teamId: string) {
  return useQuery({
    queryKey: ["reports", "team", teamId],
    queryFn: () =>
      api.get<TeamPerformanceReport>(`/reports/team-performance/${teamId}`).then((r) => r.data),
    enabled: !!teamId,
  });
}

export function useMyTeamPerformance() {
  return useQuery({
    queryKey: ["reports", "my-team"],
    queryFn: () =>
      api.get<TeamPerformanceReport>("/reports/my-team-performance").then((r) => r.data),
  });
}

export function useMarketingROI() {
  return useQuery({
    queryKey: ["reports", "marketing-roi"],
    queryFn: () => api.get<MarketingROIReport>("/reports/marketing-roi").then((r) => r.data),
  });
}

export function useConversionFunnel() {
  return useQuery({
    queryKey: ["reports", "funnel"],
    queryFn: () =>
      api.get<ConversionFunnelReport>("/reports/conversion-funnel").then((r) => r.data),
  });
}

export function useActivitySummary() {
  return useQuery({
    queryKey: ["reports", "activity-summary"],
    queryFn: () => api.get("/reports/activity-summary").then((r) => r.data),
  });
}
