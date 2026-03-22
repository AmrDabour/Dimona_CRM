export interface TierInfo {
  name: string;
  min_points: number;
  commission_pct: number;
  bonus_amount: number;
}

export interface UserMonthlyPoints {
  user_id: string;
  month: string;
  total_points: number;
  activity_points: number;
  compliance_points: number;
  conversion_points: number;
  penalty_points: number;
  tier: TierInfo;
  rank: number;
}

export interface PointTransaction {
  id: string;
  points: number;
  event_type: string;
  reference_id?: string;
  reference_type?: string;
  note?: string;
  created_at: string;
}

export interface PointTransactionPage {
  items: PointTransaction[];
  total: number;
  page: number;
  page_size: number;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  full_name: string;
  email: string;
  total_points: number;
  activity_points: number;
  compliance_points: number;
  conversion_points: number;
  penalty_points: number;
  tier: TierInfo;
}

export interface PointRule {
  id: string;
  event_type: string;
  points: number;
  category: string;
  description?: string;
  is_active: boolean;
}

export interface PenaltyRule {
  id: string;
  event_type: string;
  points: number;
  threshold_minutes?: number;
  description?: string;
  is_active: boolean;
}

export interface RulesResponse {
  point_rules: PointRule[];
  penalty_rules: PenaltyRule[];
}

export interface TierConfig {
  id: string;
  name: string;
  min_points: number;
  commission_pct: number;
  bonus_amount: number;
  perks?: Record<string, unknown>;
  sort_order: number;
}
