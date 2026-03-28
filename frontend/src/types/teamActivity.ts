import type { ActivityType } from "@/types/activity";

export interface TeamActivityItem {
  id: string;
  lead_id: string;
  lead_full_name: string;
  type: ActivityType;
  description?: string;
  scheduled_at?: string;
  is_completed: boolean;
  is_overdue: boolean;
  assigned_to?: string;
  assignee_name?: string;
  owner_user_id?: string;
  owner_name?: string;
}

export interface PaginatedTeamActivities {
  items: TeamActivityItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
