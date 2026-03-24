import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  UserMonthlyPoints,
  PointTransactionPage,
  LeaderboardEntry,
  RulesResponse,
  TierConfig,
} from "@/types/gamification";

const GAMIFICATION_KEY = "gamification";

export function useMyPoints(month?: string) {
  return useQuery({
    queryKey: [GAMIFICATION_KEY, "my-points", month],
    queryFn: () =>
      api
        .get<UserMonthlyPoints>("/gamification/my-points", {
          params: month ? { month } : undefined,
        })
        .then((r) => r.data),
  });
}

export function usePointHistory(month?: string, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: [GAMIFICATION_KEY, "history", month, page, pageSize],
    queryFn: () =>
      api
        .get<PointTransactionPage>("/gamification/my-points/history", {
          params: { month, page, page_size: pageSize },
        })
        .then((r) => r.data),
  });
}

export function useLeaderboard(month?: string, teamId?: string, limit = 20) {
  return useQuery({
    queryKey: [GAMIFICATION_KEY, "leaderboard", month, teamId, limit],
    queryFn: () =>
      api
        .get<LeaderboardEntry[]>("/gamification/leaderboard", {
          params: {
            ...(month ? { month } : {}),
            ...(teamId ? { team_id: teamId } : {}),
            limit,
          },
        })
        .then((r) => r.data),
  });
}

export function useAgentPoints(agentId: string, month?: string) {
  return useQuery({
    queryKey: [GAMIFICATION_KEY, "agent", agentId, month],
    queryFn: () =>
      api
        .get<UserMonthlyPoints>(`/gamification/agent/${agentId}/points`, {
          params: month ? { month } : undefined,
        })
        .then((r) => r.data),
    enabled: !!agentId,
  });
}

export function useAgentPointHistory(
  agentId: string,
  month?: string,
  page = 1,
  pageSize = 50,
) {
  return useQuery({
    queryKey: [GAMIFICATION_KEY, "agent-history", agentId, month, page, pageSize],
    queryFn: () =>
      api
        .get<PointTransactionPage>(
          `/gamification/agent/${agentId}/points/history`,
          { params: { month, page, page_size: pageSize } },
        )
        .then((r) => r.data),
    enabled: !!agentId,
  });
}

export function usePointRules() {
  return useQuery({
    queryKey: [GAMIFICATION_KEY, "rules"],
    queryFn: () =>
      api.get<RulesResponse>("/gamification/rules").then((r) => r.data),
  });
}

export function useTierConfig() {
  return useQuery({
    queryKey: [GAMIFICATION_KEY, "tiers"],
    queryFn: () =>
      api.get<TierConfig[]>("/gamification/tiers").then((r) => r.data),
  });
}

export function useUpdatePointRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      points,
      is_active,
    }: {
      id: string;
      points?: number;
      is_active?: boolean;
    }) =>
      api
        .patch(`/gamification/rules/point/${id}`, null, {
          params: { points, is_active },
        })
        .then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [GAMIFICATION_KEY, "rules"] }),
  });
}

export function useUpdatePenaltyRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      points,
      threshold_minutes,
      is_active,
    }: {
      id: string;
      points?: number;
      threshold_minutes?: number;
      is_active?: boolean;
    }) =>
      api
        .patch(`/gamification/rules/penalty/${id}`, null, {
          params: { points, threshold_minutes, is_active },
        })
        .then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [GAMIFICATION_KEY, "rules"] }),
  });
}

export function useUpdateTier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      min_points,
      commission_pct,
      bonus_amount,
    }: {
      id: string;
      min_points?: number;
      commission_pct?: number;
      bonus_amount?: number;
    }) =>
      api
        .patch(`/gamification/tiers/${id}`, null, {
          params: { min_points, commission_pct, bonus_amount },
        })
        .then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [GAMIFICATION_KEY, "tiers"] }),
  });
}

export function useRunComplianceCheck() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api.post("/gamification/compliance-check").then((r) => r.data),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: [GAMIFICATION_KEY] }),
  });
}
