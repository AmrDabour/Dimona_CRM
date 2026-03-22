import { useQuery, useMutation } from "@tanstack/react-query";
import api from "@/lib/api";

export function useSendWhatsApp() {
  return useMutation({
    mutationFn: (data: { lead_id: string; message: string }) =>
      api.post("/integrations/whatsapp/send", data),
  });
}

export function useGoogleAuthUrl() {
  return useQuery({
    queryKey: ["google-auth-url"],
    queryFn: () => api.get<{ url: string }>("/integrations/google/auth-url").then((r) => r.data),
    enabled: false,
  });
}

export function useGoogleCalendarStatus() {
  return useQuery({
    queryKey: ["google-calendar-status"],
    queryFn: () => api.get("/integrations/google/status").then((r) => r.data),
  });
}
