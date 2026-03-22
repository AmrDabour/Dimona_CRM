import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { UserResponse, UserCreate, UserUpdate } from "@/types/auth";
import type { PaginatedResponse } from "@/types/common";

const USERS_KEY = "users";

function getItems<T>(data: T[] | PaginatedResponse<T>): T[] {
  return Array.isArray(data) ? data : data.items;
}

export function useUsers() {
  return useQuery({
    queryKey: [USERS_KEY],
    queryFn: () =>
      api
        .get<UserResponse[] | PaginatedResponse<UserResponse>>("/users")
        .then((r) => getItems(r.data)),
  });
}

export function useUser(id: string) {
  return useQuery({
    queryKey: [USERS_KEY, id],
    queryFn: () => api.get<UserResponse>(`/users/${id}`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UserCreate) => api.post<UserResponse>("/users", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [USERS_KEY] }),
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UserUpdate }) =>
      api.patch<UserResponse>(`/users/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [USERS_KEY] }),
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/users/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [USERS_KEY] }),
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: ({ id, password }: { id: string; password: string }) =>
      api.post(`/users/${id}/reset-password`, null, {
        params: { new_password: password },
      }),
  });
}
