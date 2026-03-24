import { useTranslation } from "react-i18next";
import {
  usePendingActivities,
  useOverdueActivities,
  useCompleteActivity,
  useSyncToCalendar,
} from "@/services/activityService";
import type { Activity, ActivityType } from "@/types/activity";
import { cn, formatDateTime } from "@/lib/utils";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  Phone,
  Calendar,
  FileText,
  MessageCircle,
  Mail,
  Eye,
  RotateCw,
  CheckCircle2,
  CalendarSync,
  Inbox,
  type LucideIcon,
} from "lucide-react";

const ACTIVITY_ICONS: Record<ActivityType, LucideIcon> = {
  call: Phone,
  meeting: Calendar,
  note: FileText,
  whatsapp: MessageCircle,
  email: Mail,
  viewing: Eye,
  follow_up: RotateCw,
  status_change: RotateCw,
};

const ACTIVITY_COLORS: Record<ActivityType, string> = {
  call: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  meeting: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
  note: "bg-gray-100 text-gray-700 dark:bg-gray-800/40 dark:text-gray-300",
  whatsapp: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
  email: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300",
  viewing: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300",
  follow_up: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
  status_change: "bg-gray-100 text-gray-700 dark:bg-gray-800/40 dark:text-gray-300",
};

function ActivityCard({ activity, isOverdue }: { activity: Activity; isOverdue?: boolean }) {
  const { t } = useTranslation();
  const completeActivity = useCompleteActivity();
  const syncToCalendar = useSyncToCalendar();

  const Icon = ACTIVITY_ICONS[activity.type];
  const colorClass = ACTIVITY_COLORS[activity.type];

  function handleComplete() {
    completeActivity.mutate(activity.id, {
      onSuccess: () => toast.success(t("activities.markComplete")),
      onError: () => toast.error(t("common.error", "Something went wrong")),
    });
  }

  function handleSync() {
    syncToCalendar.mutate(activity.id, {
      onSuccess: () => toast.success(t("activities.syncCalendar")),
      onError: () => toast.error(t("common.error", "Something went wrong")),
    });
  }

  return (
    <Card className={cn(isOverdue && "border-red-300 dark:border-red-700")}>
      <CardContent className="flex items-start gap-4 p-4">
        <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-lg", colorClass)}>
          <Icon className="h-5 w-5" />
        </div>

        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {t(`activities.types.${activity.type}`, activity.type)}
            </Badge>
            {isOverdue && (
              <Badge variant="destructive" className="text-xs">
                {t("activities.overdue")}
              </Badge>
            )}
          </div>

          {activity.description && (
            <p className="text-sm">{activity.description}</p>
          )}

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
            {activity.scheduled_at && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDateTime(activity.scheduled_at)}
              </span>
            )}
            {activity.user && (
              <span>{activity.user.full_name}</span>
            )}
          </div>
        </div>

        <div className="flex shrink-0 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSync}
            disabled={syncToCalendar.isPending}
            title={t("activities.syncCalendar")}
          >
            <CalendarSync className="h-4 w-4" />
            <span className="hidden sm:inline">{t("activities.syncCalendar")}</span>
          </Button>
          <Button
            size="sm"
            onClick={handleComplete}
            disabled={completeActivity.isPending}
            title={t("activities.markComplete")}
          >
            <CheckCircle2 className="h-4 w-4" />
            <span className="hidden sm:inline">{t("activities.markComplete")}</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function ActivityListSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-24 rounded-xl" />
      ))}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
      <Inbox className="mb-3 h-12 w-12 opacity-40" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

function PendingTab() {
  const { t } = useTranslation();
  const { data: activities, isLoading } = usePendingActivities();

  if (isLoading) return <ActivityListSkeleton />;
  if (!activities?.length) return <EmptyState message={t("common.noData")} />;

  return (
    <div className="space-y-3">
      {activities.map((a) => (
        <ActivityCard key={a.id} activity={a} />
      ))}
    </div>
  );
}

function OverdueTab() {
  const { t } = useTranslation();
  const { data: activities, isLoading } = useOverdueActivities();

  if (isLoading) return <ActivityListSkeleton />;
  if (!activities?.length) return <EmptyState message={t("common.noData")} />;

  return (
    <div className="space-y-3">
      {activities.map((a) => (
        <ActivityCard key={a.id} activity={a} isOverdue />
      ))}
    </div>
  );
}

export default function ActivitiesPage() {
  const { t } = useTranslation();
  const { data: pending } = usePendingActivities();
  const { data: overdue } = useOverdueActivities();

  const pendingCount = pending?.length ?? 0;
  const overdueCount = overdue?.length ?? 0;

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold tracking-tight">
        {t("activities.title")}
      </h1>

      <Tabs defaultValue="pending">
        <TabsList>
          <TabsTrigger value="pending">
            {t("activities.pending")}
            {pendingCount > 0 && (
              <Badge variant="secondary" className="ms-2 text-xs">
                {pendingCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="overdue">
            {t("activities.overdue")}
            {overdueCount > 0 && (
              <Badge variant="destructive" className="ms-2 text-xs">
                {overdueCount}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pending">
          <PendingTab />
        </TabsContent>
        <TabsContent value="overdue">
          <OverdueTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
