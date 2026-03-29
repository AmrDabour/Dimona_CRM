import { Toaster as Sonner, type ToasterProps } from "sonner";
import { useUIStore } from "@/stores/uiStore";

export function Toaster(props: ToasterProps) {
  const theme = useUIStore((s) => s.theme);
  return (
    <Sonner theme={theme} richColors position="bottom-right" {...props} />
  );
}
