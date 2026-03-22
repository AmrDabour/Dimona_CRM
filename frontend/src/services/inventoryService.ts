import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Developer, Project, Unit, UnitSearchParams } from "@/types/inventory";
import type { PaginatedResponse, PaginationParams } from "@/types/common";

function getItems<T>(data: T[] | PaginatedResponse<T>): T[] {
  return Array.isArray(data) ? data : data.items;
}

export function useDevelopers() {
  return useQuery({
    queryKey: ["developers"],
    queryFn: () =>
      api
        .get<Developer[] | PaginatedResponse<Developer>>("/developers")
        .then((r) => getItems(r.data)),
  });
}

export function useCreateDeveloper() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string; logo_url?: string }) =>
      api.post<Developer>("/developers", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["developers"] }),
  });
}

export function useUpdateDeveloper() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Developer> }) =>
      api.patch<Developer>(`/developers/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["developers"] }),
  });
}

export function useDeleteDeveloper() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/developers/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["developers"] }),
  });
}

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () =>
      api
        .get<Project[] | PaginatedResponse<Project>>("/projects")
        .then((r) => getItems(r.data)),
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Project> & { developer_id: string; name: string }) =>
      api.post<Project>("/projects", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useUpdateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Project> }) =>
      api.patch<Project>(`/projects/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/projects/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useUnits(params?: PaginationParams & UnitSearchParams) {
  return useQuery({
    queryKey: ["units", params],
    queryFn: () =>
      api
        .get<Unit[] | PaginatedResponse<Unit>>("/units", { params })
        .then((r) => getItems(r.data)),
  });
}

export function useUnit(id: string) {
  return useQuery({
    queryKey: ["units", id],
    queryFn: () => api.get<Unit>(`/units/${id}`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateUnit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Unit> & { project_id: string }) =>
      api.post<Unit>("/units", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["units"] }),
  });
}

export function useUpdateUnit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Unit> }) =>
      api.patch<Unit>(`/units/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["units"] }),
  });
}

export function useDeleteUnit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/units/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["units"] }),
  });
}
