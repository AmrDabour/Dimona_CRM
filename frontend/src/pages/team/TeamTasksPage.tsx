import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useTeamActivities } from "@/services/teamActivityService";
import { usePermissions } from "@/hooks/usePermissions";
import { AssignTaskDialog } from "@/components/tasks/AssignTaskDialog";
import { formatDateTime } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

export default function TeamTasksPage() {
  const { t } = useTranslation();
  const permissions = usePermissions();
  const [assignTaskOpen, setAssignTaskOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [onlyToday, setOnlyToday] = useState(false);
  const [overdueOnly, setOverdueOnly] = useState(false);

  const { data, isLoading } = useTeamActivities({
    page,
    pageSize: 20,
    onlyToday,
    overdueOnly,
  });

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("teamTasks.title", "Team tasks")}
          </h1>
          <p className="text-muted-foreground">
            {t(
              "teamTasks.subtitle",
              "Scheduled follow-ups for your team (calls, meetings, viewings)",
            )}
          </p>
        </div>
        {(permissions.isAdmin || permissions.isManager) && (
          <Button variant="outline" size="sm" onClick={() => setAssignTaskOpen(true)}>
            {t("activities.assignTask")}
          </Button>
        )}
      </div>

      <AssignTaskDialog
        open={assignTaskOpen}
        onOpenChange={setAssignTaskOpen}
      />

      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Checkbox
            id="only-today"
            checked={onlyToday}
            onCheckedChange={(v) => {
              setOnlyToday(!!v);
              setPage(1);
            }}
          />
          <Label htmlFor="only-today" className="text-sm font-normal">
            {t("teamTasks.onlyToday", "Today (UTC) only")}
          </Label>
        </div>
        <div className="flex items-center gap-2">
          <Checkbox
            id="overdue-only"
            checked={overdueOnly}
            onCheckedChange={(v) => {
              setOverdueOnly(!!v);
              setPage(1);
            }}
          />
          <Label htmlFor="overdue-only" className="text-sm font-normal">
            {t("teamTasks.overdueOnly", "Overdue only")}
          </Label>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("teamTasks.tableTitle", "Upcoming & overdue")}</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          )}
          {!isLoading && data && data.items.length === 0 && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              {t("teamTasks.empty", "No scheduled tasks match your filters.")}
            </p>
          )}
          {!isLoading && data && data.items.length > 0 && (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t("teamTasks.lead")}</TableHead>
                    <TableHead>{t("teamTasks.type")}</TableHead>
                    <TableHead>{t("common.date", "When")}</TableHead>
                    <TableHead>{t("leads.assignedTo", "Assignee")}</TableHead>
                    <TableHead>{t("teamTasks.owner", "Logged by")}</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell className="font-medium">
                        <Link
                          to={`/leads/${row.lead_id}`}
                          className="text-primary hover:underline"
                        >
                          {row.lead_full_name}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <span className="capitalize">
                          {t(`activities.types.${row.type}`, row.type)}
                        </span>
                      </TableCell>
                      <TableCell>
                        {row.scheduled_at
                          ? formatDateTime(row.scheduled_at)
                          : "—"}
                        {row.is_overdue && (
                          <Badge variant="destructive" className="ms-2">
                            {t("dashboard.overdueActivities", "Overdue")}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {row.assignee_name ?? "—"}
                      </TableCell>
                      <TableCell>{row.owner_name ?? "—"}</TableCell>
                      <TableCell className="text-end">
                        <Button variant="outline" size="sm" asChild>
                          <Link to={`/leads/${row.lead_id}`}>
                            {t("teamTasks.viewLead")}
                          </Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <div className="mt-4 flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {t("common.showingOf", {
                    from: (data.page - 1) * data.page_size + 1,
                    to: Math.min(data.page * data.page_size, data.total),
                    total: data.total,
                  })}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => p - 1)}
                  >
                    {t("common.previous", "Previous")}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= data.total_pages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    {t("common.next", "Next")}
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
