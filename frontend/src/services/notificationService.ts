import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { AppNotification, NotificationListResponse } from "@/types/notification";

const NOTIFICATIONS_KEY = "notifications";
const UNREAD_COUNT_KEY = "notifications-unread-count";

export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: [UNREAD_COUNT_KEY],
    queryFn: () => api.get<{ count: number }>("/notifications/unread-count").then((r) => r.data.count),
    refetchInterval: 45_000,
    staleTime: 30_000,
  });
}

export function useNotificationsList(enabled: boolean) {
  return useQuery({
    queryKey: [NOTIFICATIONS_KEY, "list"],
    queryFn: () =>
      api.get<NotificationListResponse>("/notifications", { params: { limit: 30 } }).then((r) => r.data),
    enabled,
    refetchInterval: enabled ? 45_000 : false,
    staleTime: 15_000,
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.patch<AppNotification>(`/notifications/${id}/read`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [NOTIFICATIONS_KEY] });
      qc.invalidateQueries({ queryKey: [UNREAD_COUNT_KEY] });
    },
  });
}

export function useMarkAllNotificationsRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ count: number }>("/notifications/read-all").then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [NOTIFICATIONS_KEY] });
      qc.invalidateQueries({ queryKey: [UNREAD_COUNT_KEY] });
    },
  });
}
