import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import type { ColumnDef } from "@tanstack/react-table";
import {
  Plus,
  MoreHorizontal,
  Pencil,
  Trash2,
  Upload,
  Loader2,
} from "lucide-react";

import { cn, formatDate } from "@/lib/utils";
import { usePermissions } from "@/hooks/usePermissions";
import {
  useLeads,
  useLeadSources,
  useCreateLead,
  useUpdateLead,
  useDeleteLead,
  exportLeadsCsv,
} from "@/services/leadService";
import { useUsers } from "@/services/userService";
import type { Lead, LeadStatus } from "@/types/lead";

import { DataTable } from "@/components/shared/DataTable";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// ── Status badge colours ────────────────────────────────────────────

const STATUS_VARIANT: Record<LeadStatus, string> = {
  new: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300",
  contacted: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300",
  viewing: "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300",
  negotiation: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300",
  won: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300",
  lost: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
};

const ALL_STATUSES: LeadStatus[] = [
  "new",
  "contacted",
  "viewing",
  "negotiation",
  "won",
  "lost",
];

// ── Form schema ─────────────────────────────────────────────────────

// Keep in sync with app/schemas/lead.py (LeadCreate / LeadUpdate)
const leadFormSchema = z.object({
  full_name: z.string().min(2).max(100),
  phone: z.string().min(8).max(20),
  email: z.union([z.literal(""), z.string().email()]),
  whatsapp_number: z.union([z.literal(""), z.string().max(20)]),
  source_id: z.string().optional(),
  assigned_to: z.string().optional(),
  notes: z.string().optional(),
});

type LeadFormValues = z.infer<typeof leadFormSchema>;

function formatApiValidationDetail(err: unknown): string | null {
  const ax = err as { response?: { data?: { detail?: unknown } } };
  const detail = ax.response?.data?.detail;
  if (detail == null) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((row: { loc?: unknown[]; msg?: string }) => {
        const loc = Array.isArray(row.loc)
          ? row.loc.filter((x) => typeof x === "string" && x !== "body").join(".")
          : "";
        return loc ? `${loc}: ${row.msg ?? ""}` : (row.msg ?? "");
      })
      .filter(Boolean)
      .join("; ");
  }
  return null;
}

// ── Page Component ──────────────────────────────────────────────────

export default function LeadsPage() {
  const { t } = useTranslation();
  const permissions = usePermissions();

  // Filters & pagination state
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [sourceFilter, setSourceFilter] = useState<string>("");
  const pageSize = 10;

  // Dialog state
  const [formOpen, setFormOpen] = useState(false);
  const [editingLead, setEditingLead] = useState<Lead | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Lead | null>(null);

  // Data
  const { data: leadsData, isLoading } = useLeads({
    page,
    page_size: pageSize,
    search: search || undefined,
    status: statusFilter || undefined,
    source_id: sourceFilter || undefined,
  });
  const { data: sources } = useLeadSources();
  const { data: users } = useUsers();

  // Mutations
  const createLead = useCreateLead();
  const updateLead = useUpdateLead();
  const deleteLead = useDeleteLead();
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      await exportLeadsCsv({
        status: statusFilter || undefined,
        source_id: sourceFilter || undefined,
        search: search || undefined,
      });
      toast.success(t("leads.exportSuccess"));
    } catch {
      toast.error(t("common.error"));
    } finally {
      setExporting(false);
    }
  };

  // Form
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isSubmitting },
  } = useForm<LeadFormValues>({
    resolver: zodResolver(leadFormSchema),
    defaultValues: {
      full_name: "",
      phone: "",
      email: "",
      whatsapp_number: "",
      source_id: "",
      assigned_to: "",
      notes: "",
    },
  });

  const openCreate = () => {
    setEditingLead(null);
    reset({
      full_name: "",
      phone: "",
      email: "",
      whatsapp_number: "",
      source_id: "",
      assigned_to: "",
      notes: "",
    });
    setFormOpen(true);
  };

  const openEdit = (lead: Lead) => {
    setEditingLead(lead);
    reset({
      full_name: lead.full_name,
      phone: lead.phone,
      email: lead.email ?? "",
      whatsapp_number: lead.whatsapp_number ?? "",
      source_id: lead.source_id ?? "",
      assigned_to: lead.assigned_to ?? "",
      notes: lead.notes ?? "",
    });
    setFormOpen(true);
  };

  const onSubmit = async (values: LeadFormValues) => {
    try {
      const payload = {
        ...values,
        email: values.email || undefined,
        whatsapp_number: values.whatsapp_number || undefined,
        source_id: values.source_id || undefined,
        assigned_to: values.assigned_to || undefined,
        notes: values.notes || undefined,
      };

      if (editingLead) {
        await updateLead.mutateAsync({
          id: editingLead.id,
          data: {
            full_name: payload.full_name,
            phone: payload.phone,
            email: payload.email,
            whatsapp_number: payload.whatsapp_number,
            notes: payload.notes,
          },
        });
        toast.success(t("leads.editLead"));
      } else {
        await createLead.mutateAsync(payload);
        toast.success(t("leads.createLead"));
      }
      setFormOpen(false);
    } catch (err) {
      const v = formatApiValidationDetail(err);
      toast.error(v ?? t("common.error", "Something went wrong"));
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteLead.mutateAsync(deleteTarget.id);
      toast.success(t("common.delete"));
      setDeleteTarget(null);
    } catch {
      toast.error(t("common.error", "Something went wrong"));
    }
  };

  const handleSearch = (q: string) => {
    setSearch(q);
    setPage(1);
  };

  // ── Columns ─────────────────────────────────────────────────────

  const columns = useMemo<ColumnDef<Lead, unknown>[]>(
    () => [
      {
        accessorKey: "full_name",
        header: t("leads.fullName"),
        cell: ({ row }) => (
          <Link
            to={`/leads/${row.original.id}`}
            className="font-medium text-primary hover:underline"
          >
            {row.original.full_name}
          </Link>
        ),
      },
      {
        accessorKey: "phone",
        header: t("common.phone"),
      },
      {
        accessorKey: "status",
        header: t("common.status"),
        cell: ({ row }) => {
          const s = row.original.status;
          return (
            <Badge
              variant="secondary"
              className={cn("text-xs font-medium", STATUS_VARIANT[s])}
            >
              {t(`leads.statuses.${s}`, s)}
            </Badge>
          );
        },
      },
      {
        id: "source",
        header: t("leads.source"),
        cell: ({ row }) => row.original.source?.name ?? "—",
      },
      {
        id: "assigned",
        header: t("leads.assignedTo"),
        cell: ({ row }) => row.original.assigned_user?.full_name ?? "—",
      },
      {
        accessorKey: "created_at",
        header: t("common.date"),
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
              <DropdownMenuItem onClick={() => openEdit(row.original)}>
                <Pencil className="me-2 h-4 w-4" />
                {t("common.edit")}
              </DropdownMenuItem>
              {permissions.canDeleteLead && (
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={() => setDeleteTarget(row.original)}
                >
                  <Trash2 className="me-2 h-4 w-4" />
                  {t("common.delete")}
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        ),
      },
    ],
    [t, permissions.canDeleteLead],
  );

  // ── Render ──────────────────────────────────────────────────────

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold tracking-tight">
          {t("leads.title")}
        </h1>

        <div className="flex items-center gap-2">
          {permissions.canExportLeads && (
            <Button
              variant="outline"
              size="sm"
              disabled={exporting}
              onClick={handleExport}
            >
              {exporting ? (
                <Loader2 className="me-2 h-4 w-4 animate-spin" />
              ) : (
                <Upload className="me-2 h-4 w-4" />
              )}
              {t("common.export")}
            </Button>
          )}
          <Button size="sm" onClick={openCreate}>
            <Plus className="me-2 h-4 w-4" />
            {t("leads.createLead")}
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={statusFilter}
          onValueChange={(v) => {
            setStatusFilter(v === "ALL" ? "" : v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder={t("common.status")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">{t("common.all")}</SelectItem>
            {ALL_STATUSES.map((s) => (
              <SelectItem key={s} value={s}>
                {t(`leads.statuses.${s}`, s)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={sourceFilter}
          onValueChange={(v) => {
            setSourceFilter(v === "ALL" ? "" : v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder={t("leads.source")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">{t("common.all")}</SelectItem>
            {sources?.map((src) => (
              <SelectItem key={src.id} value={src.id}>
                {src.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <DataTable
        columns={columns}
        data={leadsData?.items ?? []}
        isLoading={isLoading}
        searchable
        onSearch={handleSearch}
        pagination={
          leadsData
            ? { page, pageSize, total: leadsData.total }
            : undefined
        }
        onPageChange={setPage}
      />

      {/* Create / Edit Dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingLead ? t("leads.editLead") : t("leads.createLead")}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>{t("leads.fullName")}</Label>
                <Input {...register("full_name")} />
                {errors.full_name && (
                  <p className="text-xs text-destructive">
                    {errors.full_name.message ||
                      `${t("leads.fullName")} ${t("validation.required", "is required")}`}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label>{t("leads.phone")}</Label>
                <Input {...register("phone")} />
                {errors.phone && (
                  <p className="text-xs text-destructive">
                    {errors.phone.message ||
                      `${t("leads.phone")} ${t("validation.required", "is required")}`}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label>{t("leads.email")}</Label>
                <Input type="email" {...register("email")} />
                {errors.email && (
                  <p className="text-xs text-destructive">
                    {t("validation.invalidEmail")}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label>{t("leads.whatsapp")}</Label>
                <Input {...register("whatsapp_number")} />
              </div>

              {!editingLead && (
                <div
                  className={cn(
                    "space-y-2",
                    !permissions.canAssignLead && "sm:col-span-2",
                  )}
                >
                  <Label>{t("leads.source")}</Label>
                  <Controller
                    control={control}
                    name="source_id"
                    render={({ field }) => (
                      <Select
                        value={field.value || undefined}
                        onValueChange={field.onChange}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={t("leads.source")} />
                        </SelectTrigger>
                        <SelectContent>
                          {sources?.map((src) => (
                            <SelectItem key={src.id} value={src.id}>
                              {src.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
              )}

              {permissions.canAssignLead && !editingLead && (
                <div className="space-y-2">
                  <Label>{t("leads.assignedTo")}</Label>
                  <Controller
                    control={control}
                    name="assigned_to"
                    render={({ field }) => (
                      <Select
                        value={field.value || undefined}
                        onValueChange={field.onChange}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={t("leads.assignedTo")} />
                        </SelectTrigger>
                        <SelectContent>
                          {users?.map((u) => (
                            <SelectItem key={u.id} value={u.id}>
                              {u.full_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
              )}
            </div>

            {/* Notes - full width */}
            <div className="space-y-2 sm:col-span-2">
              <Label>{t("leads.notes")}</Label>
              <textarea
                {...register("notes")}
                rows={3}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder={t("leads.notes")}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setFormOpen(false)}
              >
                {t("common.cancel")}
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && (
                  <Loader2 className="me-2 h-4 w-4 animate-spin" />
                )}
                {t("common.save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title={t("common.areYouSure")}
        description={t("common.thisActionCantBeUndone")}
        onConfirm={handleDelete}
        variant="destructive"
      />
    </div>
  );
}
