import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  useTeams,
  useCreateTeam,
  useUpdateTeam,
  useDeleteTeam,
  useAddTeamMember,
  useRemoveTeamMember,
  type Team,
} from "@/services/teamService";
import { useUsers } from "@/services/userService";
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
import {
  Plus,
  MoreHorizontal,
  Pencil,
  Trash2,
  UserPlus,
  UserMinus,
  ChevronDown,
  ChevronRight,
  Loader2,
} from "lucide-react";

const teamSchema = z.object({
  name: z.string().min(2),
  manager_id: z.string().optional(),
});
type TeamFormValues = z.infer<typeof teamSchema>;

export default function TeamsPage() {
  const { t } = useTranslation();
  const { data: teams, isLoading } = useTeams();
  const { data: users } = useUsers();

  const createMutation = useCreateTeam();
  const updateMutation = useUpdateTeam();
  const deleteMutation = useDeleteTeam();
  const addMemberMutation = useAddTeamMember();
  const removeMemberMutation = useRemoveTeamMember();

  const [createOpen, setCreateOpen] = useState(false);
  const [editTeam, setEditTeam] = useState<Team | null>(null);
  const [deleteTeam, setDeleteTeam] = useState<Team | null>(null);
  const [addMemberTeam, setAddMemberTeam] = useState<Team | null>(null);
  const [removeMember, setRemoveMember] = useState<{
    teamId: string;
    userId: string;
    name: string;
  } | null>(null);
  const [expandedTeamId, setExpandedTeamId] = useState<string | null>(null);
  const [selectedMemberId, setSelectedMemberId] = useState("");

  const createForm = useForm<TeamFormValues>({
    resolver: zodResolver(teamSchema),
  });

  const editForm = useForm<TeamFormValues>({
    resolver: zodResolver(teamSchema),
  });

  const managers = useMemo(
    () => users?.filter((u) => u.role === "manager" || u.role === "admin") ?? [],
    [users]
  );

  const userMap = useMemo(() => {
    const map = new Map<string, string>();
    users?.forEach((u) => map.set(u.id, u.full_name));
    return map;
  }, [users]);

  const handleOpenEdit = (team: Team) => {
    setEditTeam(team);
    editForm.reset({
      name: team.name,
      manager_id: team.manager_id ?? "",
    });
  };

  const onCreateSubmit = (data: TeamFormValues) => {
    createMutation.mutate(data, {
      onSuccess: () => {
        toast.success(t("teams.created", "Team created successfully"));
        setCreateOpen(false);
        createForm.reset();
      },
      onError: () => toast.error(t("teams.createError", "Failed to create team")),
    });
  };

  const onEditSubmit = (data: TeamFormValues) => {
    if (!editTeam) return;
    updateMutation.mutate(
      { id: editTeam.id, data },
      {
        onSuccess: () => {
          toast.success(t("teams.updated", "Team updated successfully"));
          setEditTeam(null);
        },
        onError: () => toast.error(t("teams.updateError", "Failed to update team")),
      }
    );
  };

  const onDeleteConfirm = () => {
    if (!deleteTeam) return;
    deleteMutation.mutate(deleteTeam.id, {
      onSuccess: () => {
        toast.success(t("teams.deleted", "Team deleted"));
        setDeleteTeam(null);
      },
      onError: () => toast.error(t("teams.deleteError", "Failed to delete team")),
    });
  };

  const onAddMember = () => {
    if (!addMemberTeam || !selectedMemberId) return;
    addMemberMutation.mutate(
      { teamId: addMemberTeam.id, userId: selectedMemberId },
      {
        onSuccess: () => {
          toast.success(t("teams.memberAdded", "Member added"));
          setAddMemberTeam(null);
          setSelectedMemberId("");
        },
        onError: () =>
          toast.error(t("teams.addMemberError", "Failed to add member")),
      }
    );
  };

  const onRemoveMemberConfirm = () => {
    if (!removeMember) return;
    removeMemberMutation.mutate(
      { teamId: removeMember.teamId, userId: removeMember.userId },
      {
        onSuccess: () => {
          toast.success(t("teams.memberRemoved", "Member removed"));
          setRemoveMember(null);
        },
        onError: () =>
          toast.error(t("teams.removeMemberError", "Failed to remove member")),
      }
    );
  };

  const columns = useMemo<ColumnDef<Team>[]>(
    () => [
      {
        id: "expand",
        header: "",
        cell: ({ row }) => (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() =>
              setExpandedTeamId(
                expandedTeamId === row.original.id ? null : row.original.id
              )
            }
          >
            {expandedTeamId === row.original.id ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        ),
      },
      {
        accessorKey: "name",
        header: t("teams.name", "Team Name"),
        cell: ({ row }) => (
          <span className="font-medium">{row.original.name}</span>
        ),
      },
      {
        id: "manager",
        header: t("teams.manager", "Manager"),
        cell: ({ row }) =>
          row.original.manager_id
            ? userMap.get(row.original.manager_id) ?? "—"
            : "—",
      },
      {
        id: "member_count",
        header: t("teams.members", "Members"),
        cell: ({ row }) => (
          <Badge variant="secondary">
            {row.original.members?.length ?? 0}
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
              <DropdownMenuItem
                onClick={() => setAddMemberTeam(row.original)}
              >
                <UserPlus className="mr-2 h-4 w-4" />
                {t("teams.addMember", "Add Member")}
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive"
                onClick={() => setDeleteTeam(row.original)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {t("common.delete", "Delete")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ),
      },
    ],
    [t, userMap, expandedTeamId]
  );

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("teams.title", "Teams")}
          </h1>
          <p className="text-muted-foreground">
            {t("teams.subtitle", "Manage teams and team members")}
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t("teams.createTeam", "Create Team")}
        </Button>
      </div>

      <DataTable columns={columns} data={teams ?? []} isLoading={isLoading} />

      {/* Expanded team member details */}
      {expandedTeamId && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {t("teams.teamMembers", "Team Members")} —{" "}
              {teams?.find((t) => t.id === expandedTeamId)?.name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const team = teams?.find((t) => t.id === expandedTeamId);
              const members = team?.members ?? [];
              if (members.length === 0) {
                return (
                  <p className="py-4 text-center text-sm text-muted-foreground">
                    {t("teams.noMembers", "No members in this team")}
                  </p>
                );
              }
              return (
                <div className="space-y-2">
                  {members.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between rounded-lg border p-3"
                    >
                      <div>
                        <p className="font-medium">{member.full_name}</p>
                        <p className="text-sm text-muted-foreground">
                          {member.email}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">
                          {t(`roles.${member.role}`, member.role)}
                        </Badge>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={() =>
                            setRemoveMember({
                              teamId: expandedTeamId,
                              userId: member.id,
                              name: member.full_name,
                            })
                          }
                        >
                          <UserMinus className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              );
            })()}
          </CardContent>
        </Card>
      )}

      {/* Create Team Dialog */}
      <Dialog
        open={createOpen}
        onOpenChange={(open) => {
          setCreateOpen(open);
          if (!open) createForm.reset();
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("teams.createTeam", "Create Team")}</DialogTitle>
            <DialogDescription>
              {t("teams.createDesc", "Add a new team")}
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={createForm.handleSubmit(onCreateSubmit)}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label>{t("teams.name", "Team Name")}</Label>
              <Input {...createForm.register("name")} />
              {createForm.formState.errors.name && (
                <p className="text-xs text-destructive">
                  {createForm.formState.errors.name.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("teams.manager", "Manager")}</Label>
              <Select
                value={createForm.watch("manager_id") ?? ""}
                onValueChange={(val) =>
                  createForm.setValue("manager_id", val || undefined)
                }
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={t(
                      "teams.selectManager",
                      "Select a manager"
                    )}
                  />
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

      {/* Edit Team Dialog */}
      <Dialog
        open={!!editTeam}
        onOpenChange={(open) => !open && setEditTeam(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("teams.editTeam", "Edit Team")}</DialogTitle>
            <DialogDescription>
              {t("teams.editDesc", "Update team details")}
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={editForm.handleSubmit(onEditSubmit)}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label>{t("teams.name", "Team Name")}</Label>
              <Input {...editForm.register("name")} />
              {editForm.formState.errors.name && (
                <p className="text-xs text-destructive">
                  {editForm.formState.errors.name.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("teams.manager", "Manager")}</Label>
              <Select
                value={editForm.watch("manager_id") ?? ""}
                onValueChange={(val) =>
                  editForm.setValue("manager_id", val || undefined)
                }
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={t(
                      "teams.selectManager",
                      "Select a manager"
                    )}
                  />
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
              <Button
                type="button"
                variant="outline"
                onClick={() => setEditTeam(null)}
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

      {/* Add Member Dialog */}
      <Dialog
        open={!!addMemberTeam}
        onOpenChange={(open) => {
          if (!open) {
            setAddMemberTeam(null);
            setSelectedMemberId("");
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("teams.addMember", "Add Member")}</DialogTitle>
            <DialogDescription>
              {t("teams.addMemberDesc", "Add a user to {{name}}", {
                name: addMemberTeam?.name,
              })}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>{t("teams.selectUser", "User")}</Label>
              <Select
                value={selectedMemberId}
                onValueChange={setSelectedMemberId}
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={t("teams.selectUser", "Select a user")}
                  />
                </SelectTrigger>
                <SelectContent>
                  {users
                    ?.filter(
                      (u) =>
                        !addMemberTeam?.members?.some((m) => m.id === u.id)
                    )
                    .map((u) => (
                      <SelectItem key={u.id} value={u.id}>
                        {u.full_name} ({u.email})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setAddMemberTeam(null)}
              >
                {t("common.cancel", "Cancel")}
              </Button>
              <Button
                onClick={onAddMember}
                disabled={!selectedMemberId || addMemberMutation.isPending}
              >
                {addMemberMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {t("teams.addMember", "Add Member")}
              </Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>

      {/* Remove Member Confirmation */}
      <ConfirmDialog
        open={!!removeMember}
        onOpenChange={(open) => !open && setRemoveMember(null)}
        title={t("teams.removeMemberTitle", "Remove Member")}
        description={t(
          "teams.removeMemberDesc",
          "Are you sure you want to remove {{name}} from this team?",
          { name: removeMember?.name }
        )}
        onConfirm={onRemoveMemberConfirm}
        variant="destructive"
      />

      {/* Delete Team Confirmation */}
      <ConfirmDialog
        open={!!deleteTeam}
        onOpenChange={(open) => !open && setDeleteTeam(null)}
        title={t("teams.deleteTitle", "Delete Team")}
        description={t(
          "teams.deleteDesc",
          "Are you sure you want to delete {{name}}? This action cannot be undone.",
          { name: deleteTeam?.name }
        )}
        onConfirm={onDeleteConfirm}
        variant="destructive"
      />
    </div>
  );
}
