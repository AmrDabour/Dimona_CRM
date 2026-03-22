import { Toaster as Sonner } from "sonner"
import { useUIStore } from "@/stores/uiStore"

export function Toaster() {
  const theme = useUIStore((s) => s.theme)
  return <Sonner theme={theme} richColors position="top-right" />
}
