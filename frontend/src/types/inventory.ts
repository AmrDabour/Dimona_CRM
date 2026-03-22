export type UnitStatus = "available" | "reserved" | "sold";
export type FinishingType =
  | "core_shell"
  | "semi_finished"
  | "finished";
export type PropertyType =
  | "apartment"
  | "villa"
  | "office"
  | "land"
  | "duplex"
  | "penthouse";

export interface Developer {
  id: string;
  name: string;
  description?: string;
  logo_url?: string;
  created_at: string;
  project_count?: number;
}

export interface Project {
  id: string;
  name: string;
  location?: string;
  city?: string;
  description?: string;
  developer_id: string;
  lat?: number;
  lng?: number;
  brochure_url?: string;
  created_at: string;
  developer?: { id: string; name: string };
  unit_count?: number;
}

export interface UnitImage {
  id: string;
  image_url: string;
  sort_order: number;
}

export interface Unit {
  id: string;
  unit_number: string;
  property_type: PropertyType;
  price: number;
  area_sqm: number;
  bedrooms: number;
  bathrooms: number;
  floor?: number;
  finishing: FinishingType;
  status: UnitStatus;
  notes?: string;
  specs?: Record<string, unknown>;
  project_id: string;
  created_at: string;
  project?: { id: string; name: string; location?: string; city?: string };
  images?: UnitImage[];
}

export interface UnitSearchParams {
  price_min?: number;
  price_max?: number;
  bedrooms_min?: number;
  bedrooms_max?: number;
  area_min?: number;
  area_max?: number;
  property_type?: PropertyType;
  status?: UnitStatus;
  city?: string;
  location?: string;
  developer_id?: string;
  project_id?: string;
}
