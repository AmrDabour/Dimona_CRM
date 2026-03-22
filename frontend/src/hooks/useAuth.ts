import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import api from "@/lib/api";
import type { LoginRequest, TokenResponse, UserResponse } from "@/types/auth";

export function useAuth() {
  const { setAuth, logout: storeLogout, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  const login = async (credentials: LoginRequest) => {
    const formData = new URLSearchParams();
    formData.append("username", credentials.email);
    formData.append("password", credentials.password);

    const { data: tokens } = await api.post<TokenResponse>("/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);

    const { data: user } = await api.get<UserResponse>("/users/me");
    setAuth(user, tokens.access_token, tokens.refresh_token);
    navigate("/");
  };

  const logout = () => {
    storeLogout();
    navigate("/login");
  };

  const fetchCurrentUser = async () => {
    try {
      const { data } = await api.get<UserResponse>("/users/me");
      const token = localStorage.getItem("access_token") || "";
      const refresh = localStorage.getItem("refresh_token") || "";
      setAuth(data, token, refresh);
      return data;
    } catch {
      storeLogout();
      return null;
    }
  };

  return { login, logout, fetchCurrentUser, isAuthenticated };
}
