export type ActivityType =
  | "CALL"
  | "MEETING"
  | "NOTE"
  | "WHATSAPP"
  | "EMAIL"
  | "VIEWING"
  | "FOLLOW_UP";

export interface Activity {
  id: string;
  type: ActivityType;
  description?: string;
  scheduled_at?: string;
  lead_id: string;
  user_id?: string;
  call_recording_url?: string;
  is_completed: boolean;
  google_calendar_event_id?: string;
  created_at: string;
  updated_at: string;
  user?: { id: string; full_name: string; email: string };
}

export interface ActivityCreate {
  type: ActivityType;
  description?: string;
  scheduled_at?: string;
  call_recording_url?: string;
}
