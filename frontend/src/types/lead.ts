export type LeadStatus =
  | "new"
  | "contacted"
  | "viewing"
  | "negotiation"
  | "won"
  | "lost";

export interface LeadSourceInfo {
  id: string;
  name: string;
  campaign_name?: string;
}

export interface LeadAssignedUserInfo {
  id: string;
  full_name: string;
  email: string;
}

export interface Lead {
  id: string;
  full_name: string;
  phone: string;
  email?: string;
  whatsapp_number?: string;
  status: LeadStatus;
  lost_reason?: string;
  notes?: string;
  assigned_to?: string;
  team_id?: string;
  source_id?: string;
  custom_fields?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  source?: LeadSourceInfo;
  assigned_user?: LeadAssignedUserInfo;
}

export interface LeadImportResult {
  created: number;
  failed: number;
  errors: string[];
}

export interface LeadCreate {
  full_name: string;
  phone: string;
  email?: string;
  whatsapp_number?: string;
  source_id?: string;
  assigned_to?: string;
  custom_fields?: Record<string, unknown>;
  notes?: string;
}

export interface LeadUpdate {
  full_name?: string;
  phone?: string;
  email?: string;
  whatsapp_number?: string;
  custom_fields?: Record<string, unknown>;
  notes?: string;
}

export interface LeadStatusUpdate {
  status: LeadStatus;
  note?: string;
  lost_reason?: string;
}

export interface LeadSource {
  id: string;
  name: string;
  campaign_name?: string;
  campaign_cost?: number;
  default_team_id?: string;
  created_at: string;
  lead_count?: number;
}

export interface LeadRequirement {
  id: string;
  lead_id: string;
  budget_min?: number;
  budget_max?: number;
  preferred_locations?: string[];
  min_bedrooms?: number;
  min_area_sqm?: number;
  property_type?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PipelineHistory {
  id: string;
  lead_id: string;
  from_status?: LeadStatus;
  to_status: LeadStatus;
  changed_by?: string;
  note?: string;
  created_at: string;
}
