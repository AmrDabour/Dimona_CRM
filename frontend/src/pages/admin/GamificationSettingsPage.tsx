import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  usePointRules,
  useTierConfig,
  useUpdatePointRule,
  useUpdatePenaltyRule,
  useUpdateTier,
  useRunComplianceCheck,
  useAttendanceCsvImport,
  type AttendanceImportResponse,
} from "@/services/gamificationService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Settings2, ShieldCheck, Trophy, Play, FileSpreadsheet } from "lucide-react";
import type { PointRule, PenaltyRule, TierConfig } from "@/types/gamification";

function PointRulesTab() {
  const { t } = useTranslation();
  const { data, isLoading } = usePointRules();
  const updatePoint = useUpdatePointRule();
  const updatePenalty = useUpdatePenaltyRule();
  const [editingPoints, setEditingPoints] = useState<Record<string, string>>({});

  if (isLoading) return <Skeleton className="h-[300px]" />;

  const handleSavePoints = (rule: PointRule) => {
    const val = editingPoints[rule.id];
    if (val !== undefined && val !== "") {
      updatePoint.mutate({ id: rule.id, points: parseInt(val, 10) });
      setEditingPoints((prev) => ({ ...prev, [rule.id]: "" }));
    }
  };

  const handleSavePenalty = (rule: PenaltyRule) => {
    const val = editingPoints[rule.id];
    if (val !== undefined && val !== "") {
      updatePenalty.mutate({ id: rule.id, points: parseInt(val, 10) });
      setEditingPoints((prev) => ({ ...prev, [rule.id]: "" }));
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="h-5 w-5" />
            {t("gamification.pointRules")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("gamification.eventType")}</TableHead>
                <TableHead>{t("gamification.category")}</TableHead>
                <TableHead>{t("gamification.description")}</TableHead>
                <TableHead className="w-[100px]">{t("gamification.points")}</TableHead>
                <TableHead className="w-[80px]">{t("gamification.active")}</TableHead>
                <TableHead className="w-[80px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.point_rules.map((rule) => (
                <TableRow key={rule.id}>
                  <TableCell className="font-mono text-sm">
                    {t(`gamification.events.${rule.event_type}`, {
                      defaultValue: rule.event_type,
                    })}
                  </TableCell>
                  <TableCell className="capitalize">
                    {t(`gamification.categories.${rule.category}`, {
                      defaultValue: rule.category,
                    })}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {t(`gamification.descriptions.${rule.event_type}`, {
                      defaultValue: rule.description,
                    })}
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      className="h-8 w-20"
                      defaultValue={rule.points}
                      value={editingPoints[rule.id] ?? ""}
                      placeholder={String(rule.points)}
                      onChange={(e) =>
                        setEditingPoints((prev) => ({
                          ...prev,
                          [rule.id]: e.target.value,
                        }))
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={rule.is_active}
                      onCheckedChange={(checked) =>
                        updatePoint.mutate({ id: rule.id, is_active: checked })
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleSavePoints(rule)}
                      disabled={!editingPoints[rule.id]}
                    >
                      {t("common.save")}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5" />
            {t("gamification.penaltyRules")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("gamification.eventType")}</TableHead>
                <TableHead>{t("gamification.description")}</TableHead>
                <TableHead className="w-[100px]">{t("gamification.points")}</TableHead>
                <TableHead className="w-[100px]">{t("gamification.threshold")}</TableHead>
                <TableHead className="w-[80px]">{t("gamification.active")}</TableHead>
                <TableHead className="w-[80px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.penalty_rules.map((rule) => (
                <TableRow key={rule.id}>
                  <TableCell className="font-mono text-sm">
                    {t(`gamification.events.${rule.event_type}`, {
                      defaultValue: rule.event_type,
                    })}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {t(`gamification.descriptions.${rule.event_type}`, {
                      defaultValue: rule.description,
                    })}
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      className="h-8 w-20"
                      defaultValue={rule.points}
                      value={editingPoints[rule.id] ?? ""}
                      placeholder={String(rule.points)}
                      onChange={(e) =>
                        setEditingPoints((prev) => ({
                          ...prev,
                          [rule.id]: e.target.value,
                        }))
                      }
                    />
                  </TableCell>
                  <TableCell className="text-sm">
                    {rule.threshold_minutes ? `${rule.threshold_minutes} min` : "—"}
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={rule.is_active}
                      onCheckedChange={(checked) =>
                        updatePenalty.mutate({ id: rule.id, is_active: checked })
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleSavePenalty(rule)}
                      disabled={!editingPoints[rule.id]}
                    >
                      {t("common.save")}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function AttendanceCsvTab() {
  const { t } = useTranslation();
  const importMut = useAttendanceCsvImport();
  const [sessionDate, setSessionDate] = useState(() =>
    new Date().toISOString().slice(0, 10),
  );
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<AttendanceImportResponse | null>(null);

  const runImport = (dryRun: boolean) => {
    if (!file) return;
    importMut.mutate(
      { file, sessionDate, dryRun },
      {
        onSuccess: (data) => setResult(data),
      },
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            {t("gamification.attendanceTab")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground text-sm">
            {t("gamification.attendanceHint")}
          </p>
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
            <div className="space-y-1">
              <label className="text-sm font-medium">
                {t("gamification.sessionDate")}
              </label>
              <Input
                type="date"
                value={sessionDate}
                onChange={(e) => setSessionDate(e.target.value)}
                className="w-[200px]"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">
                {t("gamification.chooseCsv")}
              </label>
              <Input
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={!file || importMut.isPending}
                onClick={() => runImport(true)}
              >
                {t("gamification.previewImport")}
              </Button>
              <Button
                disabled={!file || importMut.isPending}
                onClick={() => runImport(false)}
              >
                {t("gamification.applyPoints")}
              </Button>
            </div>
          </div>
          {importMut.isError && (
            <p className="text-sm text-destructive">
              {(importMut.error as Error)?.message || t("common.error")}
            </p>
          )}
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>{t("gamification.importResult")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {result.errors?.length > 0 && (
              <ul className="list-disc pl-5 text-sm text-destructive">
                {result.errors.map((e) => (
                  <li key={e}>{e}</li>
                ))}
              </ul>
            )}
            <div className="text-sm text-muted-foreground flex flex-wrap gap-4">
              <span>
                {t("gamification.dryRun")}:{" "}
                {result.dry_run ? t("gamification.yes") : t("gamification.no")}
              </span>
              {result.batch_id && (
                <span className="font-mono text-xs">batch: {result.batch_id}</span>
              )}
            </div>
            {result.summary && (
              <p className="text-sm">
                {Object.entries(result.summary)
                  .map(([k, v]) => `${k}=${v}`)
                  .join(" · ")}
              </p>
            )}
            {result.rows?.length > 0 && (
              <div className="rounded-md border max-h-[360px] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>#</TableHead>
                      <TableHead>{t("gamification.csvName")}</TableHead>
                      <TableHead>{t("gamification.csvAttendance")}</TableHead>
                      <TableHead>{t("gamification.status")}</TableHead>
                      <TableHead>{t("gamification.message")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.rows.map((r) => (
                      <TableRow key={`${r.line}-${r.raw_name}`}>
                        <TableCell>{r.line}</TableCell>
                        <TableCell>{r.raw_name}</TableCell>
                        <TableCell>{r.attendance_raw}</TableCell>
                        <TableCell className="font-mono text-xs">
                          {t(`gamification.rowStatus.${r.status}`, {
                            defaultValue: r.status,
                          })}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs">
                          {r.message
                            ? t(`gamification.rowMessages.${r.message}`, {
                                defaultValue: r.message,
                              })
                            : "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function TiersTab() {
  const { t } = useTranslation();
  const { data: tiers, isLoading } = useTierConfig();
  const updateTier = useUpdateTier();
  const [editing, setEditing] = useState<
    Record<string, { min_points?: string; commission_pct?: string; bonus_amount?: string }>
  >({});

  if (isLoading) return <Skeleton className="h-[200px]" />;

  const handleSave = (tier: TierConfig) => {
    const vals = editing[tier.id];
    if (!vals) return;
    updateTier.mutate({
      id: tier.id,
      min_points: vals.min_points ? parseInt(vals.min_points, 10) : undefined,
      commission_pct: vals.commission_pct
        ? parseFloat(vals.commission_pct)
        : undefined,
      bonus_amount: vals.bonus_amount
        ? parseFloat(vals.bonus_amount)
        : undefined,
    });
    setEditing((prev) => ({ ...prev, [tier.id]: {} }));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("gamification.tierConfig")}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("gamification.tier")}</TableHead>
              <TableHead>{t("gamification.minPoints")}</TableHead>
              <TableHead>{t("gamification.commissionPct")}</TableHead>
              <TableHead>{t("gamification.bonusAmount")}</TableHead>
              <TableHead className="w-[80px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tiers?.map((tier) => {
              const vals = editing[tier.id] ?? {};
              const hasChanges =
                vals.min_points || vals.commission_pct || vals.bonus_amount;
              return (
                <TableRow key={tier.id}>
                  <TableCell className="capitalize font-medium">
                    {t(`gamification.${tier.name}`, tier.name)}
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      className="h-8 w-24"
                      placeholder={String(tier.min_points)}
                      value={vals.min_points ?? ""}
                      onChange={(e) =>
                        setEditing((prev) => ({
                          ...prev,
                          [tier.id]: {
                            ...prev[tier.id],
                            min_points: e.target.value,
                          },
                        }))
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      step="0.5"
                      className="h-8 w-24"
                      placeholder={`${tier.commission_pct}%`}
                      value={vals.commission_pct ?? ""}
                      onChange={(e) =>
                        setEditing((prev) => ({
                          ...prev,
                          [tier.id]: {
                            ...prev[tier.id],
                            commission_pct: e.target.value,
                          },
                        }))
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      className="h-8 w-28"
                      placeholder={String(tier.bonus_amount)}
                      value={vals.bonus_amount ?? ""}
                      onChange={(e) =>
                        setEditing((prev) => ({
                          ...prev,
                          [tier.id]: {
                            ...prev[tier.id],
                            bonus_amount: e.target.value,
                          },
                        }))
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={!hasChanges}
                      onClick={() => handleSave(tier)}
                    >
                      {t("common.save")}
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

export default function GamificationSettingsPage() {
  const { t } = useTranslation();
  const complianceCheck = useRunComplianceCheck();
  const [resultMsg, setResultMsg] = useState("");

  const handleRunCompliance = () => {
    complianceCheck.mutate(undefined, {
      onSuccess: (data) => {
        setResultMsg(
          `${data.checked} ${t("gamification.agentsChecked")}, ${data.compliance_points_awarded} ${t("gamification.awarded")}`,
        );
      },
    });
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Settings2 className="h-6 w-6" />
            {t("gamification.settings")}
          </h1>
          <p className="text-muted-foreground">
            {t("gamification.settingsSubtitle")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {resultMsg && (
            <span className="text-sm text-emerald-600 dark:text-emerald-400">
              {resultMsg}
            </span>
          )}
          <Button
            variant="outline"
            onClick={handleRunCompliance}
            disabled={complianceCheck.isPending}
          >
            <Play className="mr-2 h-4 w-4" />
            {t("gamification.runComplianceCheck")}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="rules">
        <TabsList>
          <TabsTrigger value="rules">{t("gamification.pointRules")}</TabsTrigger>
          <TabsTrigger value="tiers">{t("gamification.tierConfig")}</TabsTrigger>
          <TabsTrigger value="attendance">{t("gamification.attendanceTab")}</TabsTrigger>
        </TabsList>
        <TabsContent value="rules" className="mt-4">
          <PointRulesTab />
        </TabsContent>
        <TabsContent value="tiers" className="mt-4">
          <TiersTab />
        </TabsContent>
        <TabsContent value="attendance" className="mt-4">
          <AttendanceCsvTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
