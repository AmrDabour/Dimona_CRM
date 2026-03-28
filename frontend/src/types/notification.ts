export interface AppNotification {
  id: string;
  type: string;
  title: string;
  body: string | null;
  lead_id: string | null;
  read_at: string | null;
  created_at: string;
  reference_type: string;
  reference_id: string;
}

export interface NotificationListResponse {
  items: AppNotification[];
  total: number;
}
