import { useMemo, useEffect } from "react";
import { useForm, Controller, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { useAuthStore } from "@/stores/authStore";
import { useUsers } from "@/services/userService";
import { useAssignManagerTask } from "@/services/activityService";
import { useLeads } from "@/services/leadService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
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

const ASSIGN_TYPES = [
  "call",
  "whatsapp",
  "meeting",
  "note",
  "email",
] as const;

/** Python weekday: 0=Mon … 6=Sun (matches backend UTC weekday). */
const WEEKDAYS_PY = [
  { v: 0, k: "mon" },
  { v: 1, k: "tue" },
  { v: 2, k: "wed" },
  { v: 3, k: "thu" },
  { v: 4, k: "fri" },
  { v: 5, k: "sat" },
  { v: 6, k: "sun" },
] as const;

function buildSchema(t: (k: string) => string) {
  return z
    .object({
      assignee_id: z.string().min(1, t("activities.assignTaskAssigneeRequired")),
      type: z.enum(ASSIGN_TYPES),
      /** "__none__" or a lead UUID when choosing from the optional client field */
      selected_lead_id: z.string().optional(),
      description: z.string().optional(),
      scheduled_at: z.string().optional(),
      task_points: z.preprocess(
        (val) => (val === "" || val == null ? 0 : val),
        z.coerce.number().min(0).max(500),
      ),
      recurrence: z.enum(["once", "weekly"]),
      weekdays: z.array(z.number().int().min(0).max(6)).default([]),
    })
    .superRefine((data, ctx) => {
      if (data.recurrence !== "weekly") return;
      const w = data.weekdays ?? [];
      if (w.length === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("activities.assignTaskWeekdaysRequired"),
          path: ["weekdays"],
        });
      }
    });
}

type FormValues = z.infer<ReturnType<typeof buildSchema>>;

interface AssignTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** When set, task is tied to this lead */
  leadId?: string;
}

function toggleWeekday(current: number[], day: number): number[] {
  if (current.includes(day)) {
    return current.filter((d) => d !== day);
  }
  return [...current, day].sort((a, b) => a - b);
}

export function AssignTaskDialog({ open, onOpenChange, leadId }: AssignTaskDialogProps) {
  const { t } = useTranslation();
  const currentUser = useAuthStore((s) => s.user);
  const { data: users } = useUsers();
  const { data: leadsPage } = useLeads({
    page: 1,
    page_size: 100,
  });
  const leads = leadsPage?.items ?? [];
  const assignMutation = useAssignManagerTask();

  const schema = useMemo(() => buildSchema(t), [t]);

  const {
    register,
    handleSubmit,
    control,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      assignee_id: "",
      type: "note",
      selected_lead_id: "__none__",
      description: "",
      scheduled_at: "",
      task_points: 0,
      recurrence: "once",
      weekdays: [],
    },
  });

  const recurrence = useWatch({ control, name: "recurrence" });

  useEffect(() => {
    if (open) {
      reset({
        assignee_id: "",
        type: "note",
        selected_lead_id: "__none__",
        description: "",
        scheduled_at: "",
        task_points: 0,
        recurrence: "once",
        weekdays: [],
      });
    }
  }, [open, reset]);

  const assignees = useMemo(() => {
    if (!users || !currentUser) return [];
    return users.filter((u) => {
      if (!u.is_active || u.id === currentUser.id) return false;
      if (u.role !== "agent") return false;
      if (currentUser.role === "manager") {
        return !!currentUser.team_id && u.team_id === currentUser.team_id;
      }
      return currentUser.role === "admin";
    });
  }, [users, currentUser]);

  const onSubmit = async (values: FormValues) => {
    try {
      let scheduledAt: string | undefined;
      if (values.scheduled_at?.trim()) {
        const d = new Date(values.scheduled_at);
        if (!Number.isNaN(d.getTime())) {
          scheduledAt = d.toISOString();
        }
      }
      const resolvedLeadId =
        leadId ??
        (values.selected_lead_id &&
        values.selected_lead_id !== "__none__"
          ? values.selected_lead_id
          : undefined);

      const result = await assignMutation.mutateAsync({
        assignee_id: values.assignee_id,
        type: values.type,
        description: values.description?.trim() || undefined,
        scheduled_at: scheduledAt,
        lead_id: resolvedLeadId,
        task_points: values.task_points,
        recurrence: values.recurrence,
        weekdays: values.recurrence === "weekly" ? values.weekdays : undefined,
      });

      if (result.schedule_id && result.activity) {
        toast.success(t("activities.assignTaskSuccessRecurringFirst"));
      } else if (result.schedule_id) {
        toast.success(t("activities.assignTaskWeeklyCreated"));
      } else {
        toast.success(t("activities.assignTaskSuccess"));
      }
      reset();
      onOpenChange(false);
    } catch {
      toast.error(t("common.error"));
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) reset();
        onOpenChange(o);
      }}
    >
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{t("activities.assignTask")}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {!leadId && (
            <p className="text-sm text-muted-foreground">
              {t("activities.assignTaskOptionalLeadIntro")}
            </p>
          )}
          {!leadId && (
            <div className="space-y-2">
              <Label>{t("activities.assignTaskLeadOptional")}</Label>
              <Controller
                control={control}
                name="selected_lead_id"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue placeholder={t("activities.assignTaskNoLead")} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">
                        {t("activities.assignTaskNoLead")}
                      </SelectItem>
                      {leads.map((l) => (
                        <SelectItem key={l.id} value={l.id}>
                          {l.full_name}
                          {l.phone ? ` · ${l.phone}` : ""}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          )}
          <div className="space-y-2">
            <Label>{t("activities.assignTaskAssignee")}</Label>
            <Controller
              control={control}
              name="assignee_id"
              render={({ field }) => (
                <Select value={field.value || undefined} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder={t("activities.assignTaskAssignee")} />
                  </SelectTrigger>
                  <SelectContent>
                    {assignees.map((u) => (
                      <SelectItem key={u.id} value={u.id}>
                        {u.full_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.assignee_id && (
              <p className="text-xs text-destructive">{errors.assignee_id.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label>{t("activities.type")}</Label>
            <Controller
              control={control}
              name="type"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ASSIGN_TYPES.map((ty) => (
                      <SelectItem key={ty} value={ty}>
                        {t(`activities.types.${ty}`, ty)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          <div className="space-y-2">
            <Label>{t("activities.assignTaskPoints")}</Label>
            <Input type="number" min={0} max={500} step={1} {...register("task_points")} />
            <p className="text-xs text-muted-foreground">{t("activities.assignTaskPointsHint")}</p>
            {errors.task_points && (
              <p className="text-xs text-destructive">{errors.task_points.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label>{t("activities.assignTaskRecurrence")}</Label>
            <Controller
              control={control}
              name="recurrence"
              render={({ field }) => (
                <Select
                  value={field.value}
                  onValueChange={(v) => {
                    field.onChange(v);
                    if (v === "once") setValue("weekdays", []);
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="once">{t("activities.assignTaskOnce")}</SelectItem>
                    <SelectItem value="weekly">{t("activities.assignTaskWeekly")}</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
            <p className="text-xs text-muted-foreground">{t("activities.assignTaskRecurrenceHint")}</p>
          </div>

          {recurrence === "weekly" && (
            <div className="space-y-2">
              <Label>{t("activities.assignTaskWeekdays")}</Label>
              <Controller
                control={control}
                name="weekdays"
                render={({ field }) => (
                  <div className="flex flex-wrap gap-3">
                    {WEEKDAYS_PY.map(({ v, k }) => (
                      <label
                        key={v}
                        className="flex cursor-pointer items-center gap-2 text-sm"
                      >
                        <Checkbox
                          checked={(field.value ?? []).includes(v)}
                          onCheckedChange={() =>
                            field.onChange(toggleWeekday(field.value ?? [], v))
                          }
                        />
                        <span>{t(`activities.weekdays.${k}`)}</span>
                      </label>
                    ))}
                  </div>
                )}
              />
              {errors.weekdays && (
                <p className="text-xs text-destructive">{errors.weekdays.message}</p>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label>{t("activities.descriptionOptional")}</Label>
            <textarea
              rows={3}
              {...register("description")}
              className={cn(
                "flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              )}
            />
          </div>

          <div className="space-y-2">
            <Label>{t("activities.scheduledOptional")}</Label>
            <Input type="datetime-local" {...register("scheduled_at")} />
            <p className="text-xs text-muted-foreground">{t("activities.assignTaskDueHint")}</p>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={isSubmitting || assignMutation.isPending}>
              {(isSubmitting || assignMutation.isPending) && (
                <Loader2 className="me-2 h-4 w-4 animate-spin" />
              )}
              {t("activities.assignTaskSubmit")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
