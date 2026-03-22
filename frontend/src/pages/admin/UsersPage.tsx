import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useResetPassword,
} from "@/services/userService";
import { useTeams } from "@/services/teamService";
import { DataTable } from "@/components/shared/DataTable";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
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
import type { UserResponse } from "@/types/auth";
import type { UserRole } from "@/stores/authStore";
import {
  Plus,
  MoreHorizontal,
  Pencil,
  Trash2,
  KeyRound,
  Loader2,
} from "lucide-react";

const createUserSchema = z.object({
  email: z.string().email(),
  full_name: z.string().min(2),
  phone: z.string().optional(),
  password: z.string().min(8),
  role: z.enum(["admin", "manager", "agent"]),
  team_id: z.string().optional(),
});
type CreateUserForm = z.infer<typeof createUserSchema>;

const editUserSchema = z.object({
  email: z.string().email(),
  full_name: z.string().min(2),
  phone: z.string().optional(),
  role: z.enum(["admin", "manager", "agent"]),
  team_id: z.string().optional(),
  is_active: z.boolean(),
});
type EditUserForm = z.infer<typeof editUserSchema>;

const resetPasswordSchema = z.object({
  password: z.string().min(8),
});
type ResetPasswordForm = z.infer<typeof resetPasswordSchema>;

const ROLE_VARIANTS: Record<UserRole, "default" | "secondary" | "outline"> = {
  admin: "default",
  manager: "secondary",
  agent: "outline",
};

export default function UsersPage() {
  const { t } = useTranslation();
  const { data: users, isLoading } = useUsers();
  const { data: teams } = useTeams();

  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();
  const deleteMutation = useDeleteUser();
  const resetPwMutation = useResetPassword();

  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState<UserResponse | null>(null);
  const [deleteUser, setDeleteUser] = useState<UserResponse | null>(null);
  const [resetPwUser, setResetPwUser] = useState<UserResponse | null>(null);

  const createForm = useForm<CreateUserForm>({
    resolver: zodResolver(createUserSchema),
    defaultValues: { role: "agent" },
  });

  const editForm = useForm<EditUserForm>({
    resolver: zodResolver(editUserSchema),
  });

  const resetPwForm = useForm<ResetPasswordForm>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const handleOpenEdit = (user: UserResponse) => {
    setEditUser(user);
    editForm.reset({
      email: user.email,
      full_name: user.full_name,
      phone: user.phone ?? "",
      role: user.role,
      team_id: user.team_id ?? "",
      is_active: user.is_active,
    });
  };

  const onCreateSubmit = (data: CreateUserForm) => {
    createMutation.mutate(data, {
      onSuccess: () => {
        toast.success(t("users.created", "User created successfully"));
        setCreateOpen(false);
        createForm.reset();
      },
      onError: () => toast.error(t("users.createError", "Failed to create user")),
    });
  };

  const onEditSubmit = (data: EditUserForm) => {
    if (!editUser) return;
    updateMutation.mutate(
      { id: editUser.id, data },
      {
        onSuccess: () => {
          toast.success(t("users.updated", "User updated successfully"));
          setEditUser(null);
        },
        onError: () => toast.error(t("users.updateError", "Failed to update user")),
      }
    );
  };

  const onDeleteConfirm = () => {
    if (!deleteUser) return;
    deleteMutation.mutate(deleteUser.id, {
      onSuccess: () => {
        toast.success(t("users.deleted", "User deleted"));
        setDeleteUser(null);
      },
      onError: () => toast.error(t("users.deleteError", "Failed to delete user")),
    });
  };

  const onResetPwSubmit = (data: ResetPasswordForm) => {
    if (!resetPwUser) return;
    resetPwMutation.mutate(
      { id: resetPwUser.id, password: data.password },
      {
        onSuccess: () => {
          toast.success(t("users.passwordReset", "Password reset successfully"));
          setResetPwUser(null);
          resetPwForm.reset();
        },
        onError: () => toast.error(t("users.resetError", "Failed to reset password")),
      }
    );
  };

  const teamMap = useMemo(() => {
    const map = new Map<string, string>();
    teams?.forEach((team) => map.set(team.id, team.name));
    return map;
  }, [teams]);

  const columns = useMemo<ColumnDef<UserResponse>[]>(
    () => [
      {
        accessorKey: "full_name",
        header: t("users.fullName", "Full Name"),
        cell: ({ row }) => (
          <span className="font-medium">{row.original.full_name}</span>
        ),
      },
      {
        accessorKey: "email",
        header: t("users.email", "Email"),
      },
      {
        accessorKey: "phone",
        header: t("users.phone", "Phone"),
        cell: ({ row }) => row.original.phone || "—",
      },
      {
        accessorKey: "role",
        header: t("users.role", "Role"),
        cell: ({ row }) => (
          <Badge variant={ROLE_VARIANTS[row.original.role]}>
            {t(`roles.${row.original.role}`, row.original.role)}
          </Badge>
        ),
      },
      {
        id: "team",
        header: t("users.team", "Team"),
        cell: ({ row }) =>
          row.original.team_id
            ? teamMap.get(row.original.team_id) ?? "—"
            : "—",
      },
      {
        accessorKey: "is_active",
        header: t("users.active", "Active"),
        cell: ({ row }) => (
          <Badge variant={row.original.is_active ? "default" : "secondary"}>
            {row.original.is_active
              ? t("common.yes", "Yes")
              : t("common.no", "No")}
          </Badge>
        ),
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
              <DropdownMenuItem onClick={() => setResetPwUser(row.original)}>
                <KeyRound className="mr-2 h-4 w-4" />
                {t("users.resetPassword", "Reset Password")}
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive"
                onClick={() => setDeleteUser(row.original)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {t("common.delete", "Delete")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ),
      },
    ],
    [t, teamMap]
  );

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("users.title", "Users")}
          </h1>
          <p className="text-muted-foreground">
            {t("users.subtitle", "Manage user accounts and roles")}
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t("users.createUser", "Create User")}
        </Button>
      </div>

      <DataTable columns={columns} data={users ?? []} isLoading={isLoading} />

      {/* Create User Dialog */}
      <Dialog
        open={createOpen}
        onOpenChange={(open) => {
          setCreateOpen(open);
          if (!open) createForm.reset();
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("users.createUser", "Create User")}</DialogTitle>
            <DialogDescription>
              {t("users.createDesc", "Add a new user to the system")}
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={createForm.handleSubmit(onCreateSubmit)}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label>{t("users.fullName", "Full Name")}</Label>
              <Input {...createForm.register("full_name")} />
              {createForm.formState.errors.full_name && (
                <p className="text-xs text-destructive">
                  {createForm.formState.errors.full_name.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("users.email", "Email")}</Label>
              <Input type="email" {...createForm.register("email")} />
              {createForm.formState.errors.email && (
                <p className="text-xs text-destructive">
                  {createForm.formState.errors.email.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("users.phone", "Phone")}</Label>
              <Input {...createForm.register("phone")} />
            </div>
            <div className="space-y-2">
              <Label>{t("users.password", "Password")}</Label>
              <Input type="password" {...createForm.register("password")} />
              {createForm.formState.errors.password && (
                <p className="text-xs text-destructive">
                  {createForm.formState.errors.password.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("users.role", "Role")}</Label>
              <Select
                value={createForm.watch("role")}
                onValueChange={(val) =>
                  createForm.setValue("role", val as UserRole)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">
                    {t("roles.admin", "Admin")}
                  </SelectItem>
                  <SelectItem value="manager">
                    {t("roles.manager", "Manager")}
                  </SelectItem>
                  <SelectItem value="agent">
                    {t("roles.agent", "Agent")}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>{t("users.team", "Team")}</Label>
              <Select
                value={createForm.watch("team_id") ?? ""}
                onValueChange={(val) =>
                  createForm.setValue("team_id", val || undefined)
                }
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={t("users.selectTeam", "Select a team")}
                  />
                </SelectTrigger>
                <SelectContent>
                  {teams?.map((team) => (
                    <SelectItem key={team.id} value={team.id}>
                      {team.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setCreateOpen(false)}
              >
                {t("common.cancel", "Cancel")}
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {t("common.create", "Create")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog
        open={!!editUser}
        onOpenChange={(open) => !open && setEditUser(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("users.editUser", "Edit User")}</DialogTitle>
            <DialogDescription>
              {t("users.editDesc", "Update user details")}
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={editForm.handleSubmit(onEditSubmit)}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label>{t("users.fullName", "Full Name")}</Label>
              <Input {...editForm.register("full_name")} />
              {editForm.formState.errors.full_name && (
                <p className="text-xs text-destructive">
                  {editForm.formState.errors.full_name.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("users.email", "Email")}</Label>
              <Input type="email" {...editForm.register("email")} />
              {editForm.formState.errors.email && (
                <p className="text-xs text-destructive">
                  {editForm.formState.errors.email.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("users.phone", "Phone")}</Label>
              <Input {...editForm.register("phone")} />
            </div>
            <div className="space-y-2">
              <Label>{t("users.role", "Role")}</Label>
              <Select
                value={editForm.watch("role")}
                onValueChange={(val) =>
                  editForm.setValue("role", val as UserRole)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">
                    {t("roles.admin", "Admin")}
                  </SelectItem>
                  <SelectItem value="manager">
                    {t("roles.manager", "Manager")}
                  </SelectItem>
                  <SelectItem value="agent">
                    {t("roles.agent", "Agent")}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>{t("users.team", "Team")}</Label>
              <Select
                value={editForm.watch("team_id") ?? ""}
                onValueChange={(val) =>
                  editForm.setValue("team_id", val || undefined)
                }
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={t("users.selectTeam", "Select a team")}
                  />
                </SelectTrigger>
                <SelectContent>
                  {teams?.map((team) => (
                    <SelectItem key={team.id} value={team.id}>
                      {team.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                {...editForm.register("is_active")}
                className="h-4 w-4 rounded border-gray-300"
              />
              <Label htmlFor="is_active">
                {t("users.isActive", "Active")}
              </Label>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setEditUser(null)}
              >
                {t("common.cancel", "Cancel")}
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {t("common.save", "Save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Reset Password Dialog */}
      <Dialog
        open={!!resetPwUser}
        onOpenChange={(open) => {
          if (!open) {
            setResetPwUser(null);
            resetPwForm.reset();
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {t("users.resetPassword", "Reset Password")}
            </DialogTitle>
            <DialogDescription>
              {t("users.resetPasswordDesc", "Set a new password for {{name}}", {
                name: resetPwUser?.full_name,
              })}
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={resetPwForm.handleSubmit(onResetPwSubmit)}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label>{t("users.newPassword", "New Password")}</Label>
              <Input type="password" {...resetPwForm.register("password")} />
              {resetPwForm.formState.errors.password && (
                <p className="text-xs text-destructive">
                  {resetPwForm.formState.errors.password.message}
                </p>
              )}
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setResetPwUser(null)}
              >
                {t("common.cancel", "Cancel")}
              </Button>
              <Button type="submit" disabled={resetPwMutation.isPending}>
                {resetPwMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {t("users.resetPassword", "Reset Password")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteUser}
        onOpenChange={(open) => !open && setDeleteUser(null)}
        title={t("users.deleteTitle", "Delete User")}
        description={t(
          "users.deleteDesc",
          "Are you sure you want to delete {{name}}? This action cannot be undone.",
          { name: deleteUser?.full_name }
        )}
        onConfirm={onDeleteConfirm}
        variant="destructive"
      />
    </div>
  );
}
