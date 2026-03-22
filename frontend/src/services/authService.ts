import { useMutation } from "@tanstack/react-query";
import api from "@/lib/api";
import type { TokenResponse } from "@/types/auth";

export function useRegisterMutation() {
  return useMutation({
    mutationFn: (data: {
      email: string;
      full_name: string;
      password: string;
      role: string;
      team_id?: string;
    }) => api.post<TokenResponse>("/auth/register", data).then((r) => r.data),
  });
}
