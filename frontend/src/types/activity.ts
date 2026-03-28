export type ActivityType =
  | "call"
  | "meeting"
  | "note"
  | "whatsapp"
  | "email"
  | "viewing"
  | "follow_up"
  | "status_change";

export interface Activity {
  id: string;
  type: ActivityType;
  description?: string;
  scheduled_at?: string;
  lead_id?: string | null;
  user_id?: string | null;
  assigned_by_id?: string | null;
  call_recording_url?: string;
  is_completed: boolean;
  google_calendar_event_id?: string;
  task_bonus_points?: number;
  manager_schedule_id?: string | null;
  created_at: string;
  updated_at: string;
  user?: { id: string; full_name: string; email: string };
  assigned_by?: { id: string; full_name: string; email: string };
}

export interface ActivityCreate {
  type: ActivityType;
  description?: string;
  scheduled_at?: string;
  call_recording_url?: string;
}

export type ManagerTaskRecurrence = "once" | "weekly";

export interface ManagerTaskAssignPayload {
  assignee_id: string;
  type: "call" | "whatsapp" | "meeting" | "note" | "email";
  description?: string;
  scheduled_at?: string;
  lead_id?: string;
  /** Bonus points when the task is delivered (0–500). */
  task_points?: number;
  recurrence?: ManagerTaskRecurrence;
  /** Weekdays 0=Mon … 6=Sun (UTC), required when recurrence is weekly. */
  weekdays?: number[];
}

export interface ManagerTaskAssignResult {
  activity?: Activity;
  schedule_id?: string | null;
  detail?: string | null;
}

/** Active recurring template from the API (weekdays UTC). */
export interface ManagerTaskSchedule {
  id: string;
  assignee_id: string;
  assignee_name: string;
  assigned_by_id: string;
  lead_id?: string | null;
  activity_type: ActivityType;
  description?: string | null;
  task_points: number;
  weekdays: number[];
  schedule_hour_utc: number;
  schedule_minute_utc: number;
  is_active: boolean;
  last_fired_on?: string | null;
}
