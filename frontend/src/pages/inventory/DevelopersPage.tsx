import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { type ColumnDef } from "@tanstack/react-table";
import { Plus, Pencil, Trash2, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { DataTable } from "@/components/shared/DataTable";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { usePermissions } from "@/hooks/usePermissions";
import {
  useDevelopers,
  useCreateDeveloper,
  useUpdateDeveloper,
  useDeleteDeveloper,
} from "@/services/inventoryService";
import { formatDate } from "@/lib/utils";
import type { Developer } from "@/types/inventory";

const developerSchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
});

type DeveloperFormValues = z.infer<typeof developerSchema>;

export default function DevelopersPage() {
  const { t } = useTranslation();
  const { canCreateInventory, canEditInventory, canDeleteInventory } =
    usePermissions();

  const { data: developers = [], isLoading } = useDevelopers();
  const createMutation = useCreateDeveloper();
  const updateMutation = useUpdateDeveloper();
  const deleteMutation = useDeleteDeveloper();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Developer | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Developer | null>(null);

  const form = useForm<DeveloperFormValues>({
    resolver: zodResolver(developerSchema),
    defaultValues: { name: "", description: "" },
  });

  const openCreate = () => {
    setEditing(null);
    form.reset({ name: "", description: "" });
    setDialogOpen(true);
  };

  const openEdit = (developer: Developer) => {
    setEditing(developer);
    form.reset({
      name: developer.name,
      description: developer.description ?? "",
    });
    setDialogOpen(true);
  };

  const onSubmit = async (values: DeveloperFormValues) => {
    try {
      if (editing) {
        await updateMutation.mutateAsync({ id: editing.id, data: values });
      } else {
        await createMutation.mutateAsync(values);
      }
      setDialogOpen(false);
      toast.success(t(editing ? "common.edit" : "common.create"));
    } catch {
      toast.error(t("common.error"));
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
      toast.success(t("common.delete"));
    } catch {
      toast.error(t("common.error"));
    } finally {
      setDeleteTarget(null);
    }
  };

  const columns = useMemo<ColumnDef<Developer, unknown>[]>(
    () => [
      {
        accessorKey: "name",
        header: t("common.name"),
      },
      {
        accessorKey: "description",
        header: t("common.description"),
        cell: ({ row }) => {
          const desc = row.original.description;
          if (!desc) return <span className="text-muted-foreground">—</span>;
          return desc.length > 60 ? `${desc.slice(0, 60)}…` : desc;
        },
      },
      {
        accessorKey: "project_count",
        header: t("inventory.projectCount"),
        cell: ({ row }) => row.original.project_count ?? 0,
      },
      {
        accessorKey: "created_at",
        header: t("common.createdAt"),
        cell: ({ row }) => formatDate(row.original.created_at),
      },
      {
        id: "actions",
        header: t("common.actions"),
        cell: ({ row }) => (
          <div className="flex items-center gap-1">
            {canEditInventory && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => openEdit(row.original)}
              >
                <Pencil className="h-4 w-4" />
              </Button>
            )}
            {canDeleteInventory && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive"
                onClick={() => setDeleteTarget(row.original)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        ),
      },
    ],
    [t, canEditInventory, canDeleteInventory],
  );

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("inventory.developers")}</h1>
        {canCreateInventory && (
          <Button onClick={openCreate}>
            <Plus className="me-2 h-4 w-4" />
            {t("inventory.createDeveloper")}
          </Button>
        )}
      </div>

      <DataTable columns={columns} data={developers} isLoading={isLoading} />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editing
                ? t("inventory.editDeveloper")
                : t("inventory.createDeveloper")}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="dev-name">{t("common.name")} *</Label>
              <Input id="dev-name" {...form.register("name")} />
              {form.formState.errors.name && (
                <p className="text-sm text-destructive">
                  {t("common.required")}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="dev-desc">{t("common.description")}</Label>
              <Input id="dev-desc" {...form.register("description")} />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setDialogOpen(false)}
              >
                {t("common.cancel")}
              </Button>
              <Button type="submit" disabled={isSaving}>
                {isSaving && (
                  <Loader2 className="me-2 h-4 w-4 animate-spin" />
                )}
                {t("common.save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

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
