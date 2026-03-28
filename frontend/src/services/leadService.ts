import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  Lead,
  LeadCreate,
  LeadUpdate,
  LeadStatusUpdate,
  LeadSource,
  LeadRequirement,
  PipelineHistory,
  LeadImportResult,
} from "@/types/lead";
import type { PaginatedResponse, PaginationParams } from "@/types/common";

const LEADS_KEY = "leads";

export function useLeads(params?: PaginationParams & { status?: string; assigned_to?: string; source_id?: string; search?: string }) {
  return useQuery({
    queryKey: [LEADS_KEY, params],
    queryFn: () => api.get<PaginatedResponse<Lead>>("/leads", { params }).then((r) => r.data),
  });
}

export function useLead(id: string) {
  return useQuery({
    queryKey: [LEADS_KEY, id],
    queryFn: () => api.get<Lead>(`/leads/${id}`).then((r) => r.data),
    enabled: !!id,
  });
}

export type LeadsExportParams = {
  status?: string;
  source_id?: string;
  assigned_to?: string;
  search?: string;
};

export async function exportLeadsCsv(params: LeadsExportParams): Promise<void> {
  const res = await api.get("/leads/export", {
    params: {
      status: params.status || undefined,
      source_id: params.source_id || undefined,
      assigned_to: params.assigned_to || undefined,
      search: params.search || undefined,
    },
    responseType: "blob",
  });
  const blob =
    res.data instanceof Blob ? res.data : new Blob([res.data as BlobPart]);
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `leads_export_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);
}

export function useImportLeads() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      return api.post<LeadImportResult>("/leads/import", fd).then((r) => r.data);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [LEADS_KEY] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
    },
  });
}

export function useCreateLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: LeadCreate) => api.post<Lead>("/leads", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [LEADS_KEY] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
    },
  });
}

export function useUpdateLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: LeadUpdate }) =>
      api.patch<Lead>(`/leads/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [LEADS_KEY] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
    },
  });
}

export function useDeleteLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/leads/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [LEADS_KEY] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
    },
  });
}

export function useUpdateLeadStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: LeadStatusUpdate }) =>
      api.patch(`/leads/${id}/status`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [LEADS_KEY] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
    },
  });
}

export function useAssignLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, assigned_to }: { id: string; assigned_to: string }) =>
      api.post(`/leads/${id}/assign`, { assigned_to }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [LEADS_KEY] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
    },
  });
}

export function usePipelineHistory(leadId: string) {
  return useQuery({
    queryKey: ["pipeline-history", leadId],
    queryFn: () =>
      api
        .get<PipelineHistory[] | { items: PipelineHistory[] }>(`/leads/${leadId}/pipeline-history`)
        .then((r) => (Array.isArray(r.data) ? r.data : r.data.items ?? [])),
    enabled: !!leadId,
  });
}

export function useLeadSources() {
  return useQuery({
    queryKey: ["lead-sources"],
    queryFn: () =>
      api
        .get<LeadSource[] | PaginatedResponse<LeadSource>>("/leads/sources/")
        .then((r) => (Array.isArray(r.data) ? r.data : r.data.items)),
  });
}

export function useLeadRequirements(leadId: string) {
  return useQuery({
    queryKey: ["lead-requirements", leadId],
    queryFn: () =>
      api
        .get<LeadRequirement[] | { items: LeadRequirement[] }>(`/leads/${leadId}/requirements`)
        .then((r) => (Array.isArray(r.data) ? r.data : r.data.items ?? [])),
    enabled: !!leadId,
  });
}

export function useCreateLeadRequirement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ leadId, data }: { leadId: string; data: Partial<LeadRequirement> }) =>
      api.post(`/leads/${leadId}/requirements`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["lead-requirements"] }),
  });
}

export function useLeadMatches(leadId: string) {
  return useQuery({
    queryKey: ["lead-matches", leadId],
    queryFn: () =>
      api
        .get(`/leads/${leadId}/matches`)
        .then((r) => {
          const payload = r.data as {
            items?: Array<{
              unit?: Record<string, unknown>;
              relevance_score?: number;
            }>;
          };

          const items = payload?.items ?? [];
          return items
            .map((entry) => {
              const unit = entry.unit ?? {};
              const project = (unit.project as Record<string, unknown> | undefined) ?? {};

              return {
                ...unit,
                relevance_score: entry.relevance_score,
                project_name: (project.name as string | undefined) ?? undefined,
                location:
                  (project.location as string | undefined) ??
                  (project.city as string | undefined) ??
                  undefined,
                total_price: (unit.price as number | undefined) ?? undefined,
              } as Record<string, unknown>;
            })
            .filter((unit) => Boolean(unit.id));
        })
        .catch((err) => {
          if (err?.response?.status === 404) {
            return [];
          }
          throw err;
        }),
    enabled: !!leadId,
  });
}
