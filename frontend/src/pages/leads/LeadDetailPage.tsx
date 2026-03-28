import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  ArrowLeft,
  Phone,
  Mail,
  MessageCircle,
  UserCheck,
  RefreshCw,
  Plus,
  CheckCircle2,
  Circle,
  Clock,
  Pencil,
  CalendarDays,
  MoveRight,
  Building2,
  BedDouble,
  Maximize2,
  MapPin,
  Loader2,
} from "lucide-react";

import { cn, formatDate, formatDateTime, formatCurrency } from "@/lib/utils";
import { usePermissions } from "@/hooks/usePermissions";
import {
  useLead,
  useUpdateLead,
  useUpdateLeadStatus,
  useAssignLead,
  useLeadSources,
  useLeadRequirements,
  useCreateLeadRequirement,
  useLeadMatches,
  usePipelineHistory,
} from "@/services/leadService";
import {
  useLeadActivities,
  useCreateActivity,
  useCompleteActivity,
} from "@/services/activityService";
import { useUsers } from "@/services/userService";
import type { Lead, LeadStatus } from "@/types/lead";
import type { Activity, ActivityType } from "@/types/activity";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { AssignTaskDialog } from "@/components/tasks/AssignTaskDialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ── Constants ───────────────────────────────────────────────────────

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

const ACTIVITY_TYPES: ActivityType[] = [
  "call",
  "meeting",
  "note",
  "whatsapp",
  "email",
  "viewing",
  "follow_up",
];

const ACTIVITY_ICON: Record<ActivityType, typeof Phone> = {
  call: Phone,
  meeting: CalendarDays,
  note: Pencil,
  whatsapp: MessageCircle,
  email: Mail,
  viewing: Building2,
  follow_up: Clock,
  status_change: Clock,
};

const REQUIREMENT_PROPERTY_TYPES = [
  "apartment",
  "villa",
  "office",
  "land",
  "duplex",
  "penthouse",
] as const;

// ── Schemas ─────────────────────────────────────────────────────────

const statusChangeSchema = z
  .object({
    status: z.string().min(1),
    note: z.string().optional(),
    lost_reason: z.string().optional(),
  })
  .refine(
    (d) => d.status !== "lost" || (d.lost_reason && d.lost_reason.length > 0),
    { path: ["lost_reason"], message: "required" },
  );

type StatusChangeValues = z.infer<typeof statusChangeSchema>;

const activitySchema = z.object({
  type: z.string().min(1),
  description: z.string().optional(),
  scheduled_at: z.string().optional(),
});

type ActivityFormValues = z.infer<typeof activitySchema>;

const optionalNumber = z.preprocess(
  (value) => {
    if (value === "" || value === null || value === undefined) return undefined;
    const asNumber = Number(value);
    return Number.isNaN(asNumber) ? undefined : asNumber;
  },
  z.number().nonnegative().optional(),
);

const requirementSchema = z.object({
  budget_min: optionalNumber,
  budget_max: optionalNumber,
  preferred_locations: z.string().optional(),
  min_bedrooms: optionalNumber,
  min_area_sqm: optionalNumber,
  property_type: z.string().optional(),
  notes: z.string().optional(),
});

type RequirementFormValues = z.infer<typeof requirementSchema>;

// ── Loading skeleton ────────────────────────────────────────────────

function DetailSkeleton() {
  return (
    <div className="space-y-6 p-6">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-[200px] rounded-xl" />
      <Skeleton className="h-[400px] rounded-xl" />
    </div>
  );
}

// ── Page ────────────────────────────────────────────────────────────

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const permissions = usePermissions();

  // Data
  const { data: lead, isLoading } = useLead(id!);
  const { data: activities } = useLeadActivities(id!);
  const { data: requirements } = useLeadRequirements(id!);
  const { data: matches } = useLeadMatches(id!);
  const { data: history } = usePipelineHistory(id!);
  const { data: users } = useUsers();

  // Mutations
  const updateStatus = useUpdateLeadStatus();
  const updateLead = useUpdateLead();
  const assignLead = useAssignLead();
  const createActivity = useCreateActivity();
  const completeActivity = useCompleteActivity();
  const createRequirement = useCreateLeadRequirement();

  const saveNotes = async () => {
    setNotesSaving(true);
    try {
      await updateLead.mutateAsync({ id: id!, data: { notes: notesValue || undefined } });
      toast.success(t("leads.notes"));
    } catch {
      toast.error(t("common.error"));
    } finally {
      setNotesSaving(false);
    }
  };

  // Dialog state
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [activityDialogOpen, setActivityDialogOpen] = useState(false);
  const [assignTaskDialogOpen, setAssignTaskDialogOpen] = useState(false);
  const [requirementDialogOpen, setRequirementDialogOpen] = useState(false);
  const [selectedAssignee, setSelectedAssignee] = useState("");
  const [notesValue, setNotesValue] = useState(lead?.notes ?? "");
  const [notesSaving, setNotesSaving] = useState(false);

  // ── Status change form ──────────────────────────────────────────

  const statusForm = useForm<StatusChangeValues>({
    resolver: zodResolver(statusChangeSchema),
    defaultValues: { status: "", note: "", lost_reason: "" },
  });

  const watchedStatus = statusForm.watch("status");

  const onStatusSubmit = async (values: StatusChangeValues) => {
    try {
      await updateStatus.mutateAsync({
        id: id!,
        data: {
          status: values.status as LeadStatus,
          note: values.note || undefined,
          lost_reason: values.lost_reason || undefined,
        },
      });
      toast.success(t("leads.changeStatus"));
      setStatusDialogOpen(false);
      statusForm.reset();
    } catch {
      toast.error(t("common.error", "Something went wrong"));
    }
  };

  // ── Assign ──────────────────────────────────────────────────────

  const onAssign = async () => {
    if (!selectedAssignee) return;
    try {
      await assignLead.mutateAsync({ id: id!, assigned_to: selectedAssignee });
      toast.success(t("leads.assign"));
      setAssignDialogOpen(false);
      setSelectedAssignee("");
    } catch {
      toast.error(t("common.error", "Something went wrong"));
    }
  };

  // ── Activity form ───────────────────────────────────────────────

  const activityForm = useForm<ActivityFormValues>({
    resolver: zodResolver(activitySchema),
    defaultValues: { type: "", description: "", scheduled_at: "" },
  });

  const onActivitySubmit = async (values: ActivityFormValues) => {
    try {
      await createActivity.mutateAsync({
        leadId: id!,
        data: {
          type: values.type as ActivityType,
          description: values.description || undefined,
          scheduled_at: values.scheduled_at || undefined,
        },
      });
      toast.success(t("activities.createActivity"));
      setActivityDialogOpen(false);
      activityForm.reset();
    } catch {
      toast.error(t("common.error", "Something went wrong"));
    }
  };

  // ── Requirement form ────────────────────────────────────────────

  const requirementForm = useForm<RequirementFormValues>({
    resolver: zodResolver(requirementSchema),
    defaultValues: {},
  });

  const onRequirementSubmit = async (values: RequirementFormValues) => {
    try {
      const normalizedPropertyType = values.property_type?.trim().toLowerCase();
      await createRequirement.mutateAsync({
        leadId: id!,
        data: {
          budget_min: values.budget_min,
          budget_max: values.budget_max,
          min_bedrooms: values.min_bedrooms,
          min_area_sqm: values.min_area_sqm,
          notes: values.notes?.trim() || undefined,
          preferred_locations: values.preferred_locations
            ? values.preferred_locations
                .split(",")
                .map((l) => l.trim())
                .filter(Boolean)
            : undefined,
          property_type:
            normalizedPropertyType &&
            REQUIREMENT_PROPERTY_TYPES.includes(
              normalizedPropertyType as (typeof REQUIREMENT_PROPERTY_TYPES)[number],
            )
              ? normalizedPropertyType
              : undefined,
        },
      });
      toast.success(t("leads.requirements"));
      setRequirementDialogOpen(false);
      requirementForm.reset();
    } catch {
      toast.error(t("common.error", "Something went wrong"));
    }
  };

  // ── Loading ─────────────────────────────────────────────────────

  if (isLoading || !lead) return <DetailSkeleton />;

  // ── Render ──────────────────────────────────────────────────────

  return (
    <div className="space-y-6 p-6">
      {/* Back + Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/leads")}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {lead.full_name}
            </h1>
            <Badge
              variant="secondary"
              className={cn("mt-1 text-xs font-medium", STATUS_VARIANT[lead.status])}
            >
              {t(`leads.statuses.${lead.status}`, lead.status)}
            </Badge>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              statusForm.reset({ status: "", note: "", lost_reason: "" });
              setStatusDialogOpen(true);
            }}
          >
            <RefreshCw className="me-2 h-4 w-4" />
            {t("leads.changeStatus")}
          </Button>

          {permissions.canAssignLead && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAssignDialogOpen(true)}
            >
              <UserCheck className="me-2 h-4 w-4" />
              {t("leads.assign")}
            </Button>
          )}

          {lead.whatsapp_number && (
            <Button variant="outline" size="sm" asChild>
              <a
                href={`https://wa.me/${lead.whatsapp_number.replace(/\D/g, "")}`}
                target="_blank"
                rel="noreferrer"
              >
                <MessageCircle className="me-2 h-4 w-4" />
                {t("leads.sendWhatsApp")}
              </a>
            </Button>
          )}
        </div>
      </div>

      {/* Info card */}
      <Card>
        <CardContent className="grid gap-4 pt-6 sm:grid-cols-2 lg:grid-cols-4">
          <InfoField label={t("leads.fullName")} value={lead.full_name} />
          <InfoField label={t("leads.phone")} value={lead.phone} />
          <InfoField label={t("leads.email")} value={lead.email} />
          <InfoField label={t("leads.whatsapp")} value={lead.whatsapp_number} />
          <InfoField label={t("leads.source")} value={lead.source?.name} />
          <InfoField
            label={t("leads.assignedTo")}
            value={lead.assigned_user?.full_name}
          />
          <InfoField label={t("common.date")} value={formatDate(lead.created_at)} />
          <InfoField
            label={t("common.status")}
            value={t(`leads.statuses.${lead.status}`, lead.status)}
          />
          {/* Notes – always visible, inline editable */}
          <div className="sm:col-span-2 lg:col-span-4 space-y-2">
            <p className="text-xs font-medium text-muted-foreground">{t("leads.notes")}</p>
            <textarea
              value={notesValue}
              onChange={(e) => setNotesValue(e.target.value)}
              rows={3}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-y min-h-[80px]"
              placeholder={t("leads.notes")}
            />
            {notesValue !== (lead.notes ?? "") && (
              <Button size="sm" onClick={saveNotes} disabled={notesSaving}>
                {notesSaving && <Loader2 className="me-2 h-4 w-4 animate-spin" />}
                {t("common.save")}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="activities" className="space-y-4">
        <TabsList>
          <TabsTrigger value="activities">{t("leads.activities")}</TabsTrigger>
          <TabsTrigger value="requirements">
            {t("leads.requirements")}
          </TabsTrigger>
          <TabsTrigger value="matching">{t("leads.matchedUnits")}</TabsTrigger>
          <TabsTrigger value="history">
            {t("leads.pipelineHistory")}
          </TabsTrigger>
        </TabsList>

        {/* ── Activities Tab ────────────────────────────────────── */}
        <TabsContent value="activities" className="space-y-4">
          <div className="flex flex-wrap justify-end gap-2">
            {(permissions.isAdmin || permissions.isManager) && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAssignTaskDialogOpen(true)}
              >
                {t("activities.assignTask")}
              </Button>
            )}
            <Button
              size="sm"
              onClick={() => {
                activityForm.reset();
                setActivityDialogOpen(true);
              }}
            >
              <Plus className="me-2 h-4 w-4" />
              {t("activities.createActivity")}
            </Button>
          </div>

          {activities && activities.length > 0 ? (
            <div className="space-y-3">
              {activities.map((act) => (
                <ActivityCard
                  key={act.id}
                  activity={act}
                  t={t}
                  onComplete={() => completeActivity.mutate(act.id)}
                />
              ))}
            </div>
          ) : (
            <EmptyState text={t("common.noData")} />
          )}
        </TabsContent>

        {/* ── Requirements Tab ──────────────────────────────────── */}
        <TabsContent value="requirements" className="space-y-4">
          <div className="flex justify-end">
            <Button
              size="sm"
              onClick={() => {
                requirementForm.reset();
                setRequirementDialogOpen(true);
              }}
            >
              <Plus className="me-2 h-4 w-4" />
              {t("leads.requirements")}
            </Button>
          </div>

          {requirements && requirements.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {requirements.map((req) => (
                <Card key={req.id}>
                  <CardContent className="grid gap-2 pt-6 text-sm">
                    {(req.budget_min != null || req.budget_max != null) && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">
                          {t("leads.budgetRange", "Budget Range")}
                        </span>
                        <span>
                          {req.budget_min != null && formatCurrency(req.budget_min)}
                          {req.budget_min != null && req.budget_max != null && " – "}
                          {req.budget_max != null && formatCurrency(req.budget_max)}
                        </span>
                      </div>
                    )}
                    {req.preferred_locations && req.preferred_locations.length > 0 && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">
                          {t("inventory.location")}
                        </span>
                        <span>{req.preferred_locations.join(", ")}</span>
                      </div>
                    )}
                    {req.min_bedrooms != null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">
                          {t("inventory.bedrooms")}
                        </span>
                        <span>{req.min_bedrooms}+</span>
                      </div>
                    )}
                    {req.property_type && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">
                          {t("inventory.propertyType")}
                        </span>
                        <span>{req.property_type}</span>
                      </div>
                    )}
                    {req.min_area_sqm != null && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">
                          {t("inventory.area")}
                        </span>
                        <span>{req.min_area_sqm}+ sqm</span>
                      </div>
                    )}
                    {req.notes && (
                      <p className="text-muted-foreground">{req.notes}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState text={t("common.noData")} />
          )}
        </TabsContent>

        {/* ── Matching Tab ──────────────────────────────────────── */}
        <TabsContent value="matching" className="space-y-4">
          {matches && (matches as unknown[]).length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {(matches as Record<string, unknown>[]).map((unit: Record<string, unknown>) => (
                <Card key={unit.id as string}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">
                      {(unit.unit_number as string) ?? t("inventory.units")}
                    </CardTitle>
                    {Boolean(unit.project_name) && (
                      <CardDescription>{String(unit.project_name)}</CardDescription>
                    )}
                  </CardHeader>
                  <CardContent className="grid gap-2 text-sm">
                    {Boolean(unit.property_type) && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Building2 className="h-4 w-4" />
                        {String(unit.property_type)}
                      </div>
                    )}
                    {unit.bedrooms != null && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <BedDouble className="h-4 w-4" />
                        {unit.bedrooms as number} {t("inventory.bedrooms")}
                      </div>
                    )}
                    {unit.area_sqm != null && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Maximize2 className="h-4 w-4" />
                        {unit.area_sqm as number} sqm
                      </div>
                    )}
                    {Boolean(unit.location) && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <MapPin className="h-4 w-4" />
                        {String(unit.location)}
                      </div>
                    )}
                    {unit.total_price != null && (
                      <p className="mt-1 font-semibold">
                        {formatCurrency(unit.total_price as number)}
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState text={t("common.noData")} />
          )}
        </TabsContent>

        {/* ── History Tab ───────────────────────────────────────── */}
        <TabsContent value="history" className="space-y-4">
          {history && history.length > 0 ? (
            <div className="relative space-y-0 ps-6">
              <div className="absolute start-[11px] top-2 bottom-2 w-px bg-border" />
              {history.map((entry) => (
                <div key={entry.id} className="relative flex gap-4 py-3">
                  <div className="absolute start-[-13px] top-4 z-10 flex h-6 w-6 items-center justify-center rounded-full border bg-background">
                    <MoveRight className="h-3 w-3 text-muted-foreground" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">
                      {entry.from_status && (
                        <>
                          <span className="text-muted-foreground">
                            {t(`leads.statuses.${entry.from_status}`, entry.from_status)}
                          </span>
                          <MoveRight className="mx-1 inline h-3 w-3" />
                        </>
                      )}
                      <span>{t(`leads.statuses.${entry.to_status}`, entry.to_status)}</span>
                    </p>
                    {entry.note && (
                      <p className="mt-0.5 text-sm text-muted-foreground">
                        {entry.note}
                      </p>
                    )}
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {formatDateTime(entry.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState text={t("common.noData")} />
          )}
        </TabsContent>
      </Tabs>

      {/* ── Status Change Dialog ────────────────────────────────── */}
      <Dialog open={statusDialogOpen} onOpenChange={setStatusDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("leads.changeStatus")}</DialogTitle>
          </DialogHeader>
          <form
            onSubmit={statusForm.handleSubmit(onStatusSubmit)}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label>{t("common.status")}</Label>
              <Controller
                control={statusForm.control}
                name="status"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue placeholder={t("common.status")} />
                    </SelectTrigger>
                    <SelectContent>
                      {ALL_STATUSES.map((s) => (
                        <SelectItem key={s} value={s}>
                          {t(`leads.statuses.${s}`, s)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div className="space-y-2">
              <Label>{t("leads.addNote")}</Label>
              <Input {...statusForm.register("note")} />
            </div>

            {watchedStatus === "LOST" && (
              <div className="space-y-2">
                <Label>{t("leads.lostReason")}</Label>
                <Input {...statusForm.register("lost_reason")} />
                {statusForm.formState.errors.lost_reason && (
                  <p className="text-xs text-destructive">
                    {t("leads.lostReason")} {t("validation.required", "is required")}
                  </p>
                )}
              </div>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setStatusDialogOpen(false)}
              >
                {t("common.cancel")}
              </Button>
              <Button
                type="submit"
                disabled={statusForm.formState.isSubmitting}
              >
                {statusForm.formState.isSubmitting && (
                  <Loader2 className="me-2 h-4 w-4 animate-spin" />
                )}
                {t("common.save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* ── Assign Dialog ───────────────────────────────────────── */}
      <Dialog open={assignDialogOpen} onOpenChange={setAssignDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("leads.assign")}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>{t("leads.assignedTo")}</Label>
              <Select
                value={selectedAssignee}
                onValueChange={setSelectedAssignee}
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
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setAssignDialogOpen(false)}
              >
                {t("common.cancel")}
              </Button>
              <Button onClick={onAssign} disabled={!selectedAssignee}>
                {t("common.save")}
              </Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>

      <AssignTaskDialog
        open={assignTaskDialogOpen}
        onOpenChange={setAssignTaskDialogOpen}
        leadId={id}
      />

      {/* ── Activity Dialog ─────────────────────────────────────── */}
      <Dialog open={activityDialogOpen} onOpenChange={setActivityDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("activities.createActivity")}</DialogTitle>
          </DialogHeader>
          <form
            onSubmit={activityForm.handleSubmit(onActivitySubmit)}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label>{t("common.status", "Type")}</Label>
              <Controller
                control={activityForm.control}
                name="type"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ACTIVITY_TYPES.map((at) => (
                        <SelectItem key={at} value={at}>
                          {t(`activities.types.${at}`, at)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div className="space-y-2">
              <Label>{t("leads.addNote", "Description")}</Label>
              <Input {...activityForm.register("description")} />
            </div>

            <div className="space-y-2">
              <Label>{t("common.date")}</Label>
              <Input
                type="datetime-local"
                {...activityForm.register("scheduled_at")}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setActivityDialogOpen(false)}
              >
                {t("common.cancel")}
              </Button>
              <Button
                type="submit"
                disabled={activityForm.formState.isSubmitting}
              >
                {activityForm.formState.isSubmitting && (
                  <Loader2 className="me-2 h-4 w-4 animate-spin" />
                )}
                {t("common.save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* ── Requirement Dialog ──────────────────────────────────── */}
      <Dialog
        open={requirementDialogOpen}
        onOpenChange={setRequirementDialogOpen}
      >
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{t("leads.requirements")}</DialogTitle>
          </DialogHeader>
          <form
            onSubmit={requirementForm.handleSubmit(onRequirementSubmit)}
            className="space-y-4"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>{t("leads.budgetMin", "Budget Min")}</Label>
                <Input
                  type="number"
                  {...requirementForm.register("budget_min")}
                />
              </div>
              <div className="space-y-2">
                <Label>{t("leads.budgetMax", "Budget Max")}</Label>
                <Input
                  type="number"
                  {...requirementForm.register("budget_max")}
                />
              </div>
              <div className="space-y-2">
                <Label>{t("inventory.location")}</Label>
                <Input
                  placeholder="Location 1, Location 2"
                  {...requirementForm.register("preferred_locations")}
                />
              </div>
              <div className="space-y-2">
                <Label>{t("inventory.bedrooms")}</Label>
                <Input
                  type="number"
                  {...requirementForm.register("min_bedrooms")}
                />
              </div>
              <div className="space-y-2">
                <Label>{t("inventory.area")}</Label>
                <Input
                  type="number"
                  {...requirementForm.register("min_area_sqm")}
                />
              </div>
              <div className="space-y-2">
                <Label>{t("inventory.propertyType")}</Label>
                <Controller
                  control={requirementForm.control}
                  name="property_type"
                  render={({ field }) => (
                    <Select
                      value={field.value || "__none__"}
                      onValueChange={(value) =>
                        field.onChange(value === "__none__" ? "" : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={t("common.select", "Select")} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none__">{t("common.all", "All")}</SelectItem>
                        {REQUIREMENT_PROPERTY_TYPES.map((pt) => (
                          <SelectItem key={pt} value={pt}>
                            {t(`inventory.propertyTypes.${pt}`, pt)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>{t("leads.addNote", "Notes")}</Label>
              <Input {...requirementForm.register("notes")} />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setRequirementDialogOpen(false)}
              >
                {t("common.cancel")}
              </Button>
              <Button
                type="submit"
                disabled={requirementForm.formState.isSubmitting}
              >
                {requirementForm.formState.isSubmitting && (
                  <Loader2 className="me-2 h-4 w-4 animate-spin" />
                )}
                {t("common.save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── Small helpers ───────────────────────────────────────────────────

function InfoField({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="text-sm">{value || "—"}</p>
    </div>
  );
}

function ActivityCard({
  activity,
  t,
  onComplete,
}: {
  activity: Activity;
  t: (key: string) => string;
  onComplete: () => void;
}) {
  const Icon = ACTIVITY_ICON[activity.type] ?? Circle;

  return (
    <Card>
      <CardContent className="flex items-start gap-4 pt-4">
        <div
          className={cn(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
            activity.is_completed
              ? "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300"
              : "bg-muted text-muted-foreground",
          )}
        >
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">
              {t(`activities.types.${activity.type}`)}
            </span>
            {activity.is_completed && (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            )}
          </div>
          {activity.description && (
            <p className="mt-0.5 text-sm text-muted-foreground">
              {activity.description}
            </p>
          )}
          <p className="mt-1 text-xs text-muted-foreground">
            {formatDateTime(activity.created_at)}
            {activity.scheduled_at && (
              <span className="ms-2">
                · {t("common.date")}: {formatDateTime(activity.scheduled_at)}
              </span>
            )}
          </p>
        </div>
        {!activity.is_completed && (
          <Button variant="ghost" size="sm" onClick={onComplete}>
            <CheckCircle2 className="me-1 h-4 w-4" />
            {t("activities.markComplete")}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex items-center justify-center rounded-lg border border-dashed py-12">
      <p className="text-sm text-muted-foreground">{text}</p>
    </div>
  );
}
