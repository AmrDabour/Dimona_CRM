import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Lead } from "@/types/lead";

interface PipelineStats {
  stages: { stage: string; label: string; count: number }[];
  total: number;
  active: number;
  conversion_rate: number;
}

interface LeadsByStageResponse {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export function usePipelineStats() {
  return useQuery({
    queryKey: ["pipeline", "stats"],
    queryFn: () => api.get<PipelineStats>("/pipeline/stats").then((r) => r.data),
  });
}

export function useLeadsByStage(status: string) {
  return useQuery({
    queryKey: ["pipeline", "stage", status],
    queryFn: () => api.get<LeadsByStageResponse>(`/pipeline/by-stage/${status}`).then((r) => r.data),
    enabled: !!status,
  });
}
