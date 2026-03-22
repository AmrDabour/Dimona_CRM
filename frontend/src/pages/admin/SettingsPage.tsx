import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  useGoogleAuthUrl,
  useGoogleCalendarStatus,
} from "@/services/integrationService";
import { useLeadSources } from "@/services/leadService";
import api from "@/lib/api";
import { DataTable } from "@/components/shared/DataTable";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { ColumnDef } from "@tanstack/react-table";
import type { LeadSource } from "@/types/lead";
import {
  Calendar,
  MessageCircle,
  ExternalLink,
  Plus,
  MoreHorizontal,
  Pencil,
  Trash2,
  Loader2,
  CheckCircle2,
  XCircle,
} from "lucide-react";

const leadSourceSchema = z.object({
  name: z.string().min(2),
  campaign_name: z.string().optional(),
  campaign_cost: z.coerce.number().min(0).optional(),
});
type LeadSourceForm = z.infer<typeof leadSourceSchema>;

export default function SettingsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data: calendarStatus } = useGoogleCalendarStatus();
  const { refetch: fetchAuthUrl } = useGoogleAuthUrl();
  const { data: leadSources, isLoading: sourcesLoading } = useLeadSources();

  const [createSourceOpen, setCreateSourceOpen] = useState(false);
  const [editSource, setEditSource] = useState<LeadSource | null>(null);
  const [deleteSource, setDeleteSource] = useState<LeadSource | null>(null);

  const createForm = useForm<LeadSourceForm>({
    resolver: zodResolver(leadSourceSchema),
  });

  const editForm = useForm<LeadSourceForm>({
    resolver: zodResolver(leadSourceSchema),
  });

  const createSourceMutation = useMutation({
    mutationFn: (data: LeadSourceForm) =>
      api.post("/leads/sources/", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lead-sources"] });
      toast.success(t("settings.sourceCreated", "Lead source created"));
      setCreateSourceOpen(false);
      createForm.reset();
    },
    onError: () =>
      toast.error(t("settings.sourceCreateError", "Failed to create source")),
  });

  const updateSourceMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: LeadSourceForm }) =>
      api.patch(`/leads/sources/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lead-sources"] });
      toast.success(t("settings.sourceUpdated", "Lead source updated"));
      setEditSource(null);
    },
    onError: () =>
      toast.error(t("settings.sourceUpdateError", "Failed to update source")),
  });

  const deleteSourceMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/leads/sources/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lead-sources"] });
      toast.success(t("settings.sourceDeleted", "Lead source deleted"));
      setDeleteSource(null);
    },
    onError: () =>
      toast.error(t("settings.sourceDeleteError", "Failed to delete source")),
  });

  const handleConnectGoogle = async () => {
    const result = await fetchAuthUrl();
    if (result.data?.url) {
      window.location.href = result.data.url;
    } else {
      toast.error(
        t("settings.googleAuthError", "Failed to get Google auth URL")
      );
    }
  };

  const handleOpenEditSource = (source: LeadSource) => {
    setEditSource(source);
    editForm.reset({
      name: source.name,
      campaign_name: source.campaign_name ?? "",
      campaign_cost: source.campaign_cost ?? 0,
    });
  };

  const isGoogleConnected = !!(calendarStatus as { connected?: boolean })
    ?.connected;

  const sourceColumns = useMemo<ColumnDef<LeadSource>[]>(
    () => [
      {
        accessorKey: "name",
        header: t("settings.sourceName", "Name"),
        cell: ({ row }) => (
          <span className="font-medium">{row.original.name}</span>
        ),
      },
      {
        accessorKey: "campaign_name",
        header: t("settings.campaignName", "Campaign"),
        cell: ({ row }) => row.original.campaign_name || "—",
      },
      {
        accessorKey: "campaign_cost",
        header: t("settings.campaignCost", "Cost"),
        cell: ({ row }) =>
          row.original.campaign_cost != null
            ? formatCurrency(row.original.campaign_cost)
            : "—",
      },
      {
        accessorKey: "lead_count",
        header: t("settings.leadCount", "Leads"),
        cell: ({ row }) => row.original.lead_count ?? 0,
      },
      {
        accessorKey: "created_at",
        header: t("common.createdAt", "Created"),
        cell: ({ row }) => formatDate(row.original.created_at),
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => handleOpenEditSource(row.original)}
              >
                <Pencil className="mr-2 h-4 w-4" />
                {t("common.edit", "Edit")}
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive"
                onClick={() => setDeleteSource(row.original)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {t("common.delete", "Delete")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ),
      },
    ],
    [t]
  );

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {t("settings.title", "Settings")}
        </h1>
        <p className="text-muted-foreground">
          {t(
            "settings.subtitle",
            "Manage integrations and system configuration"
          )}
        </p>
      </div>

      {/* Integrations Status */}
      <Card>
        <CardHeader>
          <CardTitle>
            {t("settings.integrations", "Integrations")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Google Calendar */}
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-500/10 p-2">
                <Calendar className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="font-medium">
                  {t("settings.googleCalendar", "Google Calendar")}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t(
                    "settings.googleCalendarDesc",
                    "Sync meetings and events"
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {isGoogleConnected ? (
                <Badge className="gap-1 bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/10">
                  <CheckCircle2 className="h-3 w-3" />
                  {t("settings.connected", "Connected")}
                </Badge>
              ) : (
                <>
                  <Badge
                    variant="secondary"
                    className="gap-1 text-muted-foreground"
                  >
                    <XCircle className="h-3 w-3" />
                    {t("settings.disconnected", "Disconnected")}
                  </Badge>
                  <Button size="sm" onClick={handleConnectGoogle}>
                    <ExternalLink className="mr-2 h-4 w-4" />
                    {t("settings.connect", "Connect")}
                  </Button>
                </>
              )}
            </div>
          </div>

          <Separator />

          {/* WhatsApp */}
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-emerald-500/10 p-2">
                <MessageCircle className="h-5 w-5 text-emerald-500" />
              </div>
              <div>
                <p className="font-medium">
                  {t("settings.whatsapp", "WhatsApp")}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t(
                    "settings.whatsappDesc",
                    "Send messages to leads via WhatsApp"
                  )}
                </p>
              </div>
            </div>
            <Badge
              variant="secondary"
              className="gap-1 text-muted-foreground"
            >
              {t("settings.configured", "Configured via API")}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Lead Sources */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>
            {t("settings.leadSources", "Lead Sources")}
          </CardTitle>
          <Button size="sm" onClick={() => setCreateSourceOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            {t("settings.addSource", "Add Source")}
          </Button>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={sourceColumns}
            data={leadSources ?? []}
            isLoading={sourcesLoading}
          />
        </CardContent>
      </Card>

      {/* Create Lead Source Dialog */}
      <Dialog
        open={createSourceOpen}
        onOpenChange={(open) => {
          setCreateSourceOpen(open);
          if (!open) createForm.reset();
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {t("settings.addSource", "Add Lead Source")}
            </DialogTitle>
            <DialogDescription>
              {t(
                "settings.addSourceDesc",
                "Create a new lead source for tracking"
              )}
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={createForm.handleSubmit((data) =>
              createSourceMutation.mutate(data)
            )}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label>{t("settings.sourceName", "Name")}</Label>
              <Input {...createForm.register("name")} />
              {createForm.formState.errors.name && (
                <p className="text-xs text-destructive">
                  {createForm.formState.errors.name.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("settings.campaignName", "Campaign Name")}</Label>
              <Input {...createForm.register("campaign_name")} />
            </div>
            <div className="space-y-2">
              <Label>{t("settings.campaignCost", "Campaign Cost")}</Label>
              <Input
                type="number"
                step="0.01"
                {...createForm.register("campaign_cost")}
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setCreateSourceOpen(false)}
              >
                {t("common.cancel", "Cancel")}
              </Button>
              <Button
                type="submit"
                disabled={createSourceMutation.isPending}
              >
                {createSourceMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {t("common.create", "Create")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Lead Source Dialog */}
      <Dialog
        open={!!editSource}
        onOpenChange={(open) => !open && setEditSource(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {t("settings.editSource", "Edit Lead Source")}
            </DialogTitle>
            <DialogDescription>
              {t("settings.editSourceDesc", "Update lead source details")}
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={editForm.handleSubmit((data) => {
              if (!editSource) return;
              updateSourceMutation.mutate({ id: editSource.id, data });
            })}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label>{t("settings.sourceName", "Name")}</Label>
              <Input {...editForm.register("name")} />
              {editForm.formState.errors.name && (
                <p className="text-xs text-destructive">
                  {editForm.formState.errors.name.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("settings.campaignName", "Campaign Name")}</Label>
              <Input {...editForm.register("campaign_name")} />
            </div>
            <div className="space-y-2">
              <Label>{t("settings.campaignCost", "Campaign Cost")}</Label>
              <Input
                type="number"
                step="0.01"
                {...editForm.register("campaign_cost")}
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setEditSource(null)}
              >
                {t("common.cancel", "Cancel")}
              </Button>
              <Button
                type="submit"
                disabled={updateSourceMutation.isPending}
              >
                {updateSourceMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {t("common.save", "Save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Source Confirmation */}
      <ConfirmDialog
        open={!!deleteSource}
        onOpenChange={(open) => !open && setDeleteSource(null)}
        title={t("settings.deleteSourceTitle", "Delete Lead Source")}
        description={t(
          "settings.deleteSourceDesc",
          "Are you sure you want to delete {{name}}? This action cannot be undone.",
          { name: deleteSource?.name }
        )}
        onConfirm={() => {
          if (deleteSource) deleteSourceMutation.mutate(deleteSource.id);
        }}
        variant="destructive"
      />
    </div>
  );
}
