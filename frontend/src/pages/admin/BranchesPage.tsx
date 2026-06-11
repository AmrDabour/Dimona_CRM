import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  useBranches,
  useCreateBranch,
  useUpdateBranch,
  useDeleteBranch,
  type Branch,
} from "@/hooks/useBranches";
import { useUsers } from "@/services/userService";
import { DataTable } from "@/components/shared/DataTable";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import { formatDate } from "@/lib/utils";
import type { ColumnDef } from "@tanstack/react-table";
import { Plus, MoreHorizontal, Pencil, Trash2, Loader2 } from "lucide-react";

const branchSchema = z.object({
  name: z.string().min(2),
  location: z.string().optional(),
  manager_id: z.string().optional(),
});
type BranchFormValues = z.infer<typeof branchSchema>;

export default function BranchesPage() {
  const { t } = useTranslation();
  const { data: branches, isLoading } = useBranches();
  const { data: users } = useUsers();

  const createMutation = useCreateBranch();
  const updateMutation = useUpdateBranch();
  const deleteMutation = useDeleteBranch();

  const [createOpen, setCreateOpen] = useState(false);
  const [editBranch, setEditBranch] = useState<Branch | null>(null);
  const [deleteBranch, setDeleteBranch] = useState<Branch | null>(null);

  const createForm = useForm<BranchFormValues>({
    resolver: zodResolver(branchSchema),
  });

  const editForm = useForm<BranchFormValues>({
    resolver: zodResolver(branchSchema),
  });

  const managers = useMemo(
    () =>
      users?.filter(
        (u) =>
          u.role === "branch_manager" || u.role === "admin"
      ) ?? [],
    [users]
  );

  const userMap = useMemo(() => {
    const map = new Map<string, string>();
    users?.forEach((u) => map.set(u.id, u.full_name));
    return map;
  }, [users]);

  const handleOpenEdit = (branch: Branch) => {
    setEditBranch(branch);
    editForm.reset({
      name: branch.name,
      location: branch.location ?? "",
      manager_id: branch.manager_id ?? "",
    });
  };

  const onCreateSubmit = (data: BranchFormValues) => {
    const payload = {
      ...data,
      manager_id: data.manager_id ? data.manager_id : null,
      location: data.location ? data.location : null,
    };
    // @ts-ignore
    createMutation.mutate(payload, {
      onSuccess: () => {
        toast.success(t("branches.created", "Branch created successfully"));
        setCreateOpen(false);
        createForm.reset();
      },
      onError: () => toast.error(t("branches.createError", "Failed to create branch")),
    });
  };

  const onEditSubmit = (data: BranchFormValues) => {
    if (!editBranch) return;

    const payload = {
      ...data,
      manager_id: data.manager_id ? data.manager_id : null,
      location: data.location ? data.location : null,
    };

    updateMutation.mutate(
      // @ts-ignore
      { id: editBranch.id, data: payload },
      {
        onSuccess: () => {
          toast.success(t("branches.updated", "Branch updated successfully"));
          setEditBranch(null);
        },
        onError: () => toast.error(t("branches.updateError", "Failed to update branch")),
      }
    );
  };

  const onDeleteConfirm = () => {
    if (!deleteBranch) return;

    deleteMutation.mutate(deleteBranch.id, {
      onSuccess: () => {
        toast.success(t("branches.deleted", "Branch deleted successfully"));
        setDeleteBranch(null);
      },
      onError: () => toast.error(t("branches.deleteError", "Failed to delete branch")),
    });
  };

  const columns = useMemo<ColumnDef<Branch>[]>(
    () => [
      {
        accessorKey: "name",
        header: t("branches.name", "Branch Name"),
        cell: ({ row }) => <span className="font-medium">{row.original.name}</span>,
      },
      {
        accessorKey: "location",
        header: t("branches.location", "Location"),
        cell: ({ row }) => <span>{row.original.location ?? "—"}</span>,
      },
      {
        id: "manager",
        header: t("branches.manager", "Manager"),
        cell: ({ row }) =>
          row.original.manager_id ? userMap.get(row.original.manager_id) ?? "—" : "—",
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
              <DropdownMenuItem onClick={() => handleOpenEdit(row.original)}>
                <Pencil className="mr-2 h-4 w-4" />
                {t("common.edit", "Edit")}
              </DropdownMenuItem>
              <DropdownMenuItem className="text-destructive" onClick={() => setDeleteBranch(row.original)}>
                <Trash2 className="mr-2 h-4 w-4" />
                {t("common.delete", "Delete")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ),
      },
    ],
    [t, userMap]
  );

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("branches.title", "Branches")}</h1>
          <p className="text-muted-foreground">{t("branches.subtitle", "Manage branches")}</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t("branches.createBranch", "Create Branch")}
        </Button>
      </div>

      <DataTable columns={columns} data={branches ?? []} isLoading={isLoading} />

      {/* Create Dialog */}
      <Dialog open={createOpen} onOpenChange={(open) => { setCreateOpen(open); if (!open) createForm.reset(); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("branches.createBranch", "Create Branch")}</DialogTitle>
            <DialogDescription>{t("branches.createDesc", "Add a new branch")}</DialogDescription>
          </DialogHeader>
          <form onSubmit={createForm.handleSubmit(onCreateSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label>{t("branches.name", "Branch Name")}</Label>
              <Input {...createForm.register("name")} />
              {createForm.formState.errors.name && (
                <p className="text-xs text-destructive">{createForm.formState.errors.name.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("branches.location", "Location")}</Label>
              <Input {...createForm.register("location")} />
            </div>
            <div className="space-y-2">
              <Label>{t("branches.manager", "Manager")}</Label>
              <Select
                value={createForm.watch("manager_id") ?? ""}
                onValueChange={(val) => createForm.setValue("manager_id", val || undefined)}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t("branches.selectManager", "Select a manager")} />
                </SelectTrigger>
                <SelectContent>
                  {managers.map((u) => (
                    <SelectItem key={u.id} value={u.id}>
                      {u.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>
                {t("common.cancel", "Cancel")}
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {t("common.create", "Create")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={!!editBranch} onOpenChange={(open) => !open && setEditBranch(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("branches.editBranch", "Edit Branch")}</DialogTitle>
            <DialogDescription>{t("branches.editDesc", "Update branch details")}</DialogDescription>
          </DialogHeader>
          <form onSubmit={editForm.handleSubmit(onEditSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label>{t("branches.name", "Branch Name")}</Label>
              <Input {...editForm.register("name")} />
              {editForm.formState.errors.name && (
                <p className="text-xs text-destructive">{editForm.formState.errors.name.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("branches.location", "Location")}</Label>
              <Input {...editForm.register("location")} />
            </div>
            <div className="space-y-2">
              <Label>{t("branches.manager", "Manager")}</Label>
              <Select
                value={editForm.watch("manager_id") ?? ""}
                onValueChange={(val) => editForm.setValue("manager_id", val || undefined)}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t("branches.selectManager", "Select a manager")} />
                </SelectTrigger>
                <SelectContent>
                  {managers.map((u) => (
                    <SelectItem key={u.id} value={u.id}>
                      {u.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditBranch(null)}>
                {t("common.cancel", "Cancel")}
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {t("common.save", "Save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteBranch}
        onOpenChange={(open) => !open && setDeleteBranch(null)}
        title={t("branches.deleteConfirm", "Delete Branch")}
        description={t(
          "branches.deleteWarning",
          "Are you sure you want to delete this branch? This action cannot be undone."
        )}
        onConfirm={onDeleteConfirm}
        variant="destructive"
      />
    </div>
  );
}
