export interface TierInfo {
  name: string;
  min_points: number;
  commission_pct: number;
  bonus_amount: number;
}

export interface DashboardGamification {
  total_points: number;
  tier: TierInfo;
  rank: number;
  activity_points: number;
  compliance_points: number;
  conversion_points: number;
  penalty_points: number;
}

export interface DashboardSummary {
  user: { id: string; name: string; role: string };
  pipeline: Record<string, number>;
  leads: { new_today: number; new_this_week: number; total_active: number };
  activities: { pending: number; overdue: number };
  gamification?: DashboardGamification;
  generated_at: string;
}

export interface AgentPerformanceReport {
  agent: { id: string; name: string; email?: string };
  period: { start: string; end: string };
  leads: {
    total: number;
    won: number;
    lost: number;
    active: number;
    pipeline_breakdown: Record<string, number>;
  };
  activities: { total: number; calls: number; meetings: number };
  metrics: {
    conversion_rate: number;
    win_rate: number;
    avg_response_hours?: number;
  };
}

export interface TeamPerformanceReport {
  team: { id: string; name: string };
  period: { start: string; end: string };
  summary: {
    total_leads: number;
    won_leads: number;
    conversion_rate: number;
    member_count: number;
  };
  agents: Array<{
    agent_id: string;
    name: string;
    total_leads: number;
    won_leads: number;
    conversion_rate: number;
  }>;
}

export interface SourceROI {
  source_id: string;
  source_name: string;
  campaign_name?: string;
  campaign_cost: number;
  total_leads: number;
  won_leads: number;
  lost_leads: number;
  cost_per_lead: number;
  cost_per_won: number;
  conversion_rate: number;
}

export interface MarketingROIReport {
  period: { start: string; end: string };
  summary: {
    total_campaign_cost: number;
    total_leads: number;
    total_won: number;
    avg_cost_per_lead: number;
    avg_cost_per_won: number;
    overall_conversion: number;
  };
  sources: SourceROI[];
}

export interface FunnelStage {
  stage: string;
  count: number;
  drop_off_rate?: number;
}

export interface ConversionFunnelReport {
  period_days: number;
  funnel: FunnelStage[];
  summary: {
    total_leads: number;
    total_won: number;
    total_lost: number;
    overall_conversion: number;
  };
}
