import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { PaginatedTeamActivities } from "@/types/teamActivity";

export function useTeamActivities(options: {
  page?: number;
  pageSize?: number;
  onlyToday?: boolean;
  overdueOnly?: boolean;
}) {
  const { page = 1, pageSize = 20, onlyToday = false, overdueOnly = false } = options;
  return useQuery({
    queryKey: ["team", "activities", page, pageSize, onlyToday, overdueOnly],
    queryFn: () =>
      api
        .get<PaginatedTeamActivities>("/team/activities", {
          params: {
            page,
            page_size: pageSize,
            only_today: onlyToday,
            overdue_only: overdueOnly,
          },
        })
        .then((r) => r.data),
  });
}
