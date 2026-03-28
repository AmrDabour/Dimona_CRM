import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  Activity,
  ActivityCreate,
  ManagerTaskAssignPayload,
  ManagerTaskAssignResult,
  ManagerTaskSchedule,
} from "@/types/activity";
import type { PaginatedResponse } from "@/types/common";

function getItems<T>(data: T[] | PaginatedResponse<T> | { items: T[] }): T[] {
  return Array.isArray(data) ? data : data.items;
}

export function useLeadActivities(leadId: string) {
  return useQuery({
    queryKey: ["activities", "lead", leadId],
    queryFn: () =>
      api
        .get<Activity[] | PaginatedResponse<Activity>>(`/leads/${leadId}/activities`)
        .then((r) => getItems(r.data)),
    enabled: !!leadId,
  });
}

export function useCreateActivity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ leadId, data }: { leadId: string; data: ActivityCreate }) =>
      api.post<Activity>(`/leads/${leadId}/activities`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["activities"] }),
  });
}

export function useAssignManagerTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ManagerTaskAssignPayload) =>
      api
        .post<ManagerTaskAssignResult>("/activities/assign", {
          assignee_id: body.assignee_id,
          type: body.type,
          description: body.description,
          scheduled_at: body.scheduled_at,
          lead_id: body.lead_id || undefined,
          task_points: body.task_points ?? 0,
          recurrence: body.recurrence ?? "once",
          weekdays:
            body.recurrence === "weekly" ? body.weekdays : undefined,
        })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["activities"] });
      qc.invalidateQueries({ queryKey: ["activities", "manager-schedules"] });
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });
}

export function useManagerTaskSchedules(enabled = true) {
  return useQuery({
    queryKey: ["activities", "manager-schedules"],
    queryFn: () =>
      api
        .get<ManagerTaskSchedule[]>("/activities/manager-schedules")
        .then((r) => r.data),
    enabled,
  });
}

export function useCancelManagerTaskSchedule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (scheduleId: string) =>
      api.post(`/activities/manager-schedules/${scheduleId}/cancel`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["activities", "manager-schedules"] });
    },
  });
}

export function usePendingActivities() {
  return useQuery({
    queryKey: ["activities", "pending"],
    queryFn: () =>
      api
        .get<Activity[] | PaginatedResponse<Activity>>("/activities/pending/")
        .then((r) => getItems(r.data)),
  });
}

export function useOverdueActivities() {
  return useQuery({
    queryKey: ["activities", "overdue"],
    queryFn: () =>
      api
        .get<Activity[] | { items: Activity[] }>("/activities/overdue/")
        .then((r) => getItems(r.data)),
  });
}

export function useCompleteActivity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post(`/activities/${id}/complete`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["activities"] }),
  });
}

export function useSyncToCalendar() {
  return useMutation({
    mutationFn: (activityId: string) =>
      api.post("/integrations/calendar/sync-activity", { activity_id: activityId }),
  });
}
