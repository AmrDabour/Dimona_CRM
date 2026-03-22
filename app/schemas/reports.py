from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel


class AgentInfo(BaseModel):
    id: str
    name: str
    email: Optional[str] = None


class PeriodInfo(BaseModel):
    start: str
    end: str


class LeadStats(BaseModel):
    total: int
    won: int
    lost: int
    active: int
    pipeline_breakdown: Dict[str, int]


class ActivityStats(BaseModel):
    total: int
    calls: int
    meetings: int


class PerformanceMetrics(BaseModel):
    conversion_rate: float
    win_rate: float
    avg_response_hours: Optional[float] = None


class AgentPerformanceReport(BaseModel):
    agent: AgentInfo
    period: PeriodInfo
    leads: LeadStats
    activities: ActivityStats
    metrics: PerformanceMetrics


class AgentSummary(BaseModel):
    agent_id: str
    name: str
    total_leads: int
    won_leads: int
    conversion_rate: float


class TeamInfo(BaseModel):
    id: str
    name: str


class TeamSummary(BaseModel):
    total_leads: int
    won_leads: int
    conversion_rate: float
    member_count: int


class TeamPerformanceReport(BaseModel):
    team: TeamInfo
    period: PeriodInfo
    summary: TeamSummary
    agents: List[AgentSummary]


class SourceROI(BaseModel):
    source_id: str
    source_name: str
    campaign_name: Optional[str]
    campaign_cost: float
    total_leads: int
    won_leads: int
    lost_leads: int
    cost_per_lead: float
    cost_per_won: float
    conversion_rate: float


class MarketingROISummary(BaseModel):
    total_campaign_cost: float
    total_leads: int
    total_won: int
    avg_cost_per_lead: float
    avg_cost_per_won: float
    overall_conversion: float


class MarketingROIReport(BaseModel):
    period: PeriodInfo
    summary: MarketingROISummary
    sources: List[SourceROI]


class FunnelStage(BaseModel):
    stage: str
    count: int
    drop_off_rate: Optional[float] = None


class FunnelSummary(BaseModel):
    total_leads: int
    total_won: int
    total_lost: int
    overall_conversion: float


class ConversionFunnelReport(BaseModel):
    period_days: int
    funnel: List[FunnelStage]
    summary: FunnelSummary


class DashboardUser(BaseModel):
    id: str
    name: str
    role: str


class DashboardLeads(BaseModel):
    new_today: int
    new_this_week: int
    total_active: int


class DashboardActivities(BaseModel):
    pending: int
    overdue: int


class DashboardSummary(BaseModel):
    user: DashboardUser
    pipeline: Dict[str, int]
    leads: DashboardLeads
    activities: DashboardActivities
    generated_at: str
