import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { type ColumnDef } from "@tanstack/react-table";
import { Plus, Pencil, Trash2, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  useProjects,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
  useDevelopers,
} from "@/services/inventoryService";
import { formatDate } from "@/lib/utils";
import type { Project } from "@/types/inventory";

const projectSchema = z.object({
  name: z.string().min(1),
  developer_id: z.string().min(1),
  location: z.string().optional(),
  city: z.string().optional(),
  description: z.string().optional(),
});

type ProjectFormValues = z.infer<typeof projectSchema>;

export default function ProjectsPage() {
  const { t } = useTranslation();
  const { canCreateInventory, canEditInventory, canDeleteInventory } =
    usePermissions();

  const { data: projects = [], isLoading } = useProjects();
  const { data: developers = [] } = useDevelopers();
  const createMutation = useCreateProject();
  const updateMutation = useUpdateProject();
  const deleteMutation = useDeleteProject();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Project | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null);

  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: "",
      developer_id: "",
      location: "",
      city: "",
      description: "",
    },
  });

  const openCreate = () => {
    setEditing(null);
    form.reset({
      name: "",
      developer_id: "",
      location: "",
      city: "",
      description: "",
    });
    setDialogOpen(true);
  };

  const openEdit = (project: Project) => {
    setEditing(project);
    form.reset({
      name: project.name,
      developer_id: project.developer_id,
      location: project.location ?? "",
      city: project.city ?? "",
      description: project.description ?? "",
    });
    setDialogOpen(true);
  };

  const onSubmit = async (values: ProjectFormValues) => {
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

  const columns = useMemo<ColumnDef<Project, unknown>[]>(
    () => [
      {
        accessorKey: "name",
        header: t("common.name"),
      },
      {
        id: "developer",
        header: t("inventory.developer"),
        cell: ({ row }) =>
          row.original.developer?.name ?? (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        accessorKey: "location",
        header: t("inventory.location"),
        cell: ({ row }) =>
          row.original.location || (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        accessorKey: "city",
        header: t("inventory.city"),
        cell: ({ row }) =>
          row.original.city || (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        accessorKey: "unit_count",
        header: t("inventory.unitCount"),
        cell: ({ row }) => row.original.unit_count ?? 0,
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
        <h1 className="text-2xl font-bold">{t("inventory.projects")}</h1>
        {canCreateInventory && (
          <Button onClick={openCreate}>
            <Plus className="me-2 h-4 w-4" />
            {t("inventory.createProject")}
          </Button>
        )}
      </div>

      <DataTable columns={columns} data={projects} isLoading={isLoading} />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editing
                ? t("inventory.editProject")
                : t("inventory.createProject")}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="proj-name">{t("common.name")} *</Label>
              <Input id="proj-name" {...form.register("name")} />
              {form.formState.errors.name && (
                <p className="text-sm text-destructive">
                  {t("common.required")}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label>{t("inventory.developer")} *</Label>
              <Controller
                control={form.control}
                name="developer_id"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue
                        placeholder={t("inventory.developer")}
                      />
                    </SelectTrigger>
                    <SelectContent>
                      {developers.map((dev) => (
                        <SelectItem key={dev.id} value={dev.id}>
                          {dev.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {form.formState.errors.developer_id && (
                <p className="text-sm text-destructive">
                  {t("common.required")}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="proj-location">
                  {t("inventory.location")}
                </Label>
                <Input
                  id="proj-location"
                  {...form.register("location")}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="proj-city">{t("inventory.city")}</Label>
                <Input id="proj-city" {...form.register("city")} />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="proj-desc">{t("common.description")}</Label>
              <Input id="proj-desc" {...form.register("description")} />
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
