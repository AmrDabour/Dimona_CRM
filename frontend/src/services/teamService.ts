import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { PaginatedResponse } from "@/types/common";

export interface Team {
  id: string;
  name: string;
  manager_id?: string;
  created_at: string;
  members?: Array<{ id: string; email: string; full_name: string; role: string }>;
}

const TEAMS_KEY = "teams";

function getItems<T>(data: T[] | PaginatedResponse<T>): T[] {
  return Array.isArray(data) ? data : data.items;
}

export function useTeams() {
  return useQuery({
    queryKey: [TEAMS_KEY],
    queryFn: () =>
      api
        .get<Team[] | PaginatedResponse<Team>>("/teams")
        .then((r) => getItems(r.data)),
  });
}

export function useTeam(id: string) {
  return useQuery({
    queryKey: [TEAMS_KEY, id],
    queryFn: () => api.get<Team>(`/teams/${id}`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; manager_id?: string }) =>
      api.post<Team>("/teams", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TEAMS_KEY] }),
  });
}

export function useUpdateTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; manager_id?: string } }) =>
      api.patch<Team>(`/teams/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TEAMS_KEY] }),
  });
}

export function useDeleteTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/teams/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TEAMS_KEY] }),
  });
}

export function useAddTeamMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ teamId, userId }: { teamId: string; userId: string }) =>
      api.post(`/teams/${teamId}/members/${userId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TEAMS_KEY] }),
  });
}

export function useRemoveTeamMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ teamId, userId }: { teamId: string; userId: string }) =>
      api.delete(`/teams/${teamId}/members/${userId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TEAMS_KEY] }),
  });
}
