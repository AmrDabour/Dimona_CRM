import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Bell } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { arSA, enUS } from "date-fns/locale";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  useUnreadNotificationCount,
  useNotificationsList,
  useMarkNotificationRead,
  useMarkAllNotificationsRead,
} from "@/services/notificationService";
import type { AppNotification } from "@/types/notification";

export function NotificationBell() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const { data: unread = 0 } = useUnreadNotificationCount();
  const { data: listData, isLoading } = useNotificationsList(open);
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllNotificationsRead();

  const locale = i18n.language === "ar" ? arSA : enUS;
  const items = listData?.items ?? [];

  const handleOpenItem = (n: AppNotification) => {
    markRead.mutate(n.id);
    setOpen(false);
    if (n.lead_id) {
      navigate(`/leads/${n.lead_id}`);
      return;
    }
    if (n.reference_type === "activity" && n.reference_id) {
      navigate(`/activities?activityId=${n.reference_id}`);
    }
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative h-9 w-9 shrink-0 text-foreground hover:bg-accent"
          aria-label={t("notifications.ariaLabel")}
          title={t("notifications.title")}
        >
          <Bell className="h-5 w-5" strokeWidth={2.25} />
          {unread > 0 && (
            <span
              className={cn(
                "absolute -end-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold text-destructive-foreground",
              )}
            >
              {unread > 99 ? "99+" : unread}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80" sideOffset={8}>
        <DropdownMenuLabel className="flex items-center justify-between gap-2">
          <span>{t("notifications.title")}</span>
          {unread > 0 && (
            <button
              type="button"
              className="text-xs font-normal text-primary hover:underline"
              onClick={() => markAll.mutate()}
              disabled={markAll.isPending}
            >
              {t("notifications.markAllRead")}
            </button>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {isLoading && (
          <div className="px-2 py-6 text-center text-sm text-muted-foreground">
            …
          </div>
        )}
        {!isLoading && items.length === 0 && (
          <div className="px-2 py-6 text-center text-sm text-muted-foreground">
            {t("notifications.empty")}
          </div>
        )}
        <div className="max-h-72 overflow-y-auto">
          {items.map((n) => (
            <DropdownMenuItem
              key={n.id}
              className={cn(
                "flex cursor-pointer flex-col items-stretch gap-0.5 px-3 py-2.5",
                !n.read_at && "bg-muted/50",
              )}
              onClick={() => handleOpenItem(n)}
            >
              <span className="text-sm font-medium leading-tight">{n.title}</span>
              {n.body && (
                <span className="text-xs text-muted-foreground leading-snug">
                  {n.body}
                </span>
              )}
              <span className="text-[10px] text-muted-foreground mt-0.5">
                {formatDistanceToNow(new Date(n.created_at), {
                  addSuffix: true,
                  locale,
                })}
              </span>
            </DropdownMenuItem>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
