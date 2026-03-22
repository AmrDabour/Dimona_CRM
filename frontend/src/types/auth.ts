import type { UserRole } from "@/stores/authStore";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  role: UserRole;
  team_id?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  full_name: string;
  phone?: string;
  password: string;
  role: UserRole;
  team_id?: string;
}

export interface UserUpdate {
  email?: string;
  full_name?: string;
  phone?: string;
  role?: UserRole;
  team_id?: string;
  is_active?: boolean;
}
