import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Lead } from "@/types/lead";

export function usePipelineStats() {
  return useQuery({
    queryKey: ["pipeline", "stats"],
    queryFn: () => api.get<Record<string, number>>("/pipeline/stats").then((r) => r.data),
  });
}

export function useLeadsByStage(status: string) {
  return useQuery({
    queryKey: ["pipeline", "stage", status],
    queryFn: () => api.get<Lead[]>(`/pipeline/by-stage/${status}`).then((r) => r.data),
    enabled: !!status,
  });
}
