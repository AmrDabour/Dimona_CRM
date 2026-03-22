import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { type ColumnDef } from "@tanstack/react-table";
import { Plus, Pencil, Trash2, Loader2, SlidersHorizontal, X } from "lucide-react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
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
  useUnits,
  useCreateUnit,
  useUpdateUnit,
  useDeleteUnit,
  useProjects,
} from "@/services/inventoryService";
import { formatCurrency, formatDate } from "@/lib/utils";
import type {
  Unit,
  UnitStatus,
  PropertyType,
  FinishingType,
  UnitSearchParams,
} from "@/types/inventory";

const PROPERTY_TYPES: PropertyType[] = [
  "apartment",
  "villa",
  "office",
  "land",
  "duplex",
  "penthouse",
];

const FINISHING_TYPES: FinishingType[] = [
  "core_shell",
  "semi_finished",
  "finished",
];

const UNIT_STATUSES: UnitStatus[] = ["available", "reserved", "sold"];

const STATUS_COLORS: Record<UnitStatus, string> = {
  available: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
  reserved: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
  sold: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
};

const unitSchema = z.object({
  unit_number: z.string().min(1),
  project_id: z.string().min(1),
  property_type: z.string().min(1),
  price: z.coerce.number().min(0),
  area_sqm: z.coerce.number().min(0),
  bedrooms: z.coerce.number().int().min(0),
  bathrooms: z.coerce.number().int().min(0),
  floor: z.coerce.number().int().optional(),
  finishing: z.string().min(1),
  status: z.string().min(1),
  notes: z.string().optional(),
});

type UnitFormValues = z.infer<typeof unitSchema>;

const EMPTY_FILTERS: UnitSearchParams = {};

export default function UnitsPage() {
  const { t } = useTranslation();
  const { canCreateInventory, canEditInventory, canDeleteInventory } =
    usePermissions();

  const [filters, setFilters] = useState<UnitSearchParams>(EMPTY_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const { data: units = [], isLoading } = useUnits(filters);
  const { data: projects = [] } = useProjects();
  const createMutation = useCreateUnit();
  const updateMutation = useUpdateUnit();
  const deleteMutation = useDeleteUnit();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Unit | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Unit | null>(null);

  const form = useForm<UnitFormValues>({
    resolver: zodResolver(unitSchema),
    defaultValues: {
      unit_number: "",
      project_id: "",
      property_type: "apartment",
      price: 0,
      area_sqm: 0,
      bedrooms: 0,
      bathrooms: 0,
      floor: undefined,
      finishing: "core_shell",
      status: "available",
      notes: "",
    },
  });

  const openCreate = () => {
    setEditing(null);
    form.reset({
      unit_number: "",
      project_id: "",
      property_type: "apartment",
      price: 0,
      area_sqm: 0,
      bedrooms: 0,
      bathrooms: 0,
      floor: undefined,
      finishing: "core_shell",
      status: "available",
      notes: "",
    });
    setDialogOpen(true);
  };

  const openEdit = (unit: Unit) => {
    setEditing(unit);
    form.reset({
      unit_number: unit.unit_number,
      project_id: unit.project_id,
      property_type: unit.property_type,
      price: unit.price,
      area_sqm: unit.area_sqm,
      bedrooms: unit.bedrooms,
      bathrooms: unit.bathrooms,
      floor: unit.floor ?? undefined,
      finishing: unit.finishing,
      status: unit.status,
      notes: unit.notes ?? "",
    });
    setDialogOpen(true);
  };

  const onSubmit = async (values: UnitFormValues) => {
    try {
      const payload = {
        ...values,
        property_type: values.property_type as PropertyType,
        finishing: values.finishing as FinishingType,
        status: values.status as UnitStatus,
      };
      if (editing) {
        await updateMutation.mutateAsync({ id: editing.id, data: payload });
      } else {
        await createMutation.mutateAsync(payload);
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

  const updateFilter = (patch: Partial<UnitSearchParams>) => {
    setFilters((prev) => ({ ...prev, ...patch }));
  };

  const clearFilters = () => {
    setFilters(EMPTY_FILTERS);
  };

  const hasActiveFilters = Object.values(filters).some(
    (v) => v !== undefined && v !== "",
  );

  const columns = useMemo<ColumnDef<Unit, unknown>[]>(
    () => [
      {
        accessorKey: "unit_number",
        header: t("inventory.unitNumber"),
      },
      {
        id: "project",
        header: t("inventory.project"),
        cell: ({ row }) =>
          row.original.project?.name ?? (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        accessorKey: "property_type",
        header: t("inventory.propertyType"),
        cell: ({ row }) =>
          t(`inventory.propertyTypes.${row.original.property_type}`),
      },
      {
        accessorKey: "price",
        header: t("inventory.price"),
        cell: ({ row }) => formatCurrency(row.original.price),
      },
      {
        accessorKey: "area_sqm",
        header: t("inventory.area"),
      },
      {
        accessorKey: "bedrooms",
        header: t("inventory.bedrooms"),
      },
      {
        accessorKey: "bathrooms",
        header: t("inventory.bathrooms"),
      },
      {
        accessorKey: "floor",
        header: t("inventory.floor"),
        cell: ({ row }) =>
          row.original.floor ?? (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        accessorKey: "finishing",
        header: t("inventory.finishing"),
        cell: ({ row }) =>
          t(`inventory.finishingTypes.${row.original.finishing}`),
      },
      {
        accessorKey: "status",
        header: t("common.status"),
        cell: ({ row }) => (
          <Badge
            variant="outline"
            className={cn(
              "border-transparent",
              STATUS_COLORS[row.original.status],
            )}
          >
            {t(`inventory.unitStatuses.${row.original.status}`)}
          </Badge>
        ),
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
        <h1 className="text-2xl font-bold">{t("inventory.units")}</h1>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => setFiltersOpen((o) => !o)}
          >
            <SlidersHorizontal className="me-2 h-4 w-4" />
            {t("common.filters")}
          </Button>
          {canCreateInventory && (
            <Button onClick={openCreate}>
              <Plus className="me-2 h-4 w-4" />
              {t("inventory.createUnit")}
            </Button>
          )}
        </div>
      </div>

      {filtersOpen && (
        <div className="rounded-lg border bg-card p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">{t("common.filters")}</h3>
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="me-2 h-3 w-3" />
                {t("common.clearFilters")}
              </Button>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            <div className="space-y-1.5">
              <Label className="text-xs">{t("inventory.minPrice")}</Label>
              <Input
                type="number"
                placeholder="0"
                value={filters.price_min ?? ""}
                onChange={(e) =>
                  updateFilter({
                    price_min: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  })
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">{t("inventory.maxPrice")}</Label>
              <Input
                type="number"
                placeholder="∞"
                value={filters.price_max ?? ""}
                onChange={(e) =>
                  updateFilter({
                    price_max: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  })
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">{t("inventory.minBedrooms")}</Label>
              <Input
                type="number"
                placeholder="0"
                value={filters.bedrooms_min ?? ""}
                onChange={(e) =>
                  updateFilter({
                    bedrooms_min: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  })
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">{t("inventory.maxBedrooms")}</Label>
              <Input
                type="number"
                placeholder="∞"
                value={filters.bedrooms_max ?? ""}
                onChange={(e) =>
                  updateFilter({
                    bedrooms_max: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  })
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">{t("inventory.minArea")}</Label>
              <Input
                type="number"
                placeholder="0"
                value={filters.area_min ?? ""}
                onChange={(e) =>
                  updateFilter({
                    area_min: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  })
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">{t("inventory.maxArea")}</Label>
              <Input
                type="number"
                placeholder="∞"
                value={filters.area_max ?? ""}
                onChange={(e) =>
                  updateFilter({
                    area_max: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  })
                }
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">{t("inventory.propertyType")}</Label>
              <Select
                value={filters.property_type ?? "ALL"}
                onValueChange={(v) =>
                  updateFilter({
                    property_type:
                      v === "ALL" ? undefined : (v as PropertyType),
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">{t("common.all")}</SelectItem>
                  {PROPERTY_TYPES.map((pt) => (
                    <SelectItem key={pt} value={pt}>
                      {t(`inventory.propertyTypes.${pt}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">{t("common.status")}</Label>
              <Select
                value={filters.status ?? "ALL"}
                onValueChange={(v) =>
                  updateFilter({
                    status: v === "ALL" ? undefined : (v as UnitStatus),
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">{t("common.all")}</SelectItem>
                  {UNIT_STATUSES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {t(`inventory.unitStatuses.${s}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">{t("inventory.city")}</Label>
              <Input
                placeholder={t("inventory.city")}
                value={filters.city ?? ""}
                onChange={(e) =>
                  updateFilter({
                    city: e.target.value || undefined,
                  })
                }
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">{t("inventory.project")}</Label>
              <Select
                value={filters.project_id ?? "ALL"}
                onValueChange={(v) =>
                  updateFilter({
                    project_id: v === "ALL" ? undefined : v,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">{t("common.all")}</SelectItem>
                  {projects.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      )}

      <DataTable columns={columns} data={units} isLoading={isLoading} />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editing
                ? t("inventory.editUnit")
                : t("inventory.createUnit")}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="unit-number">
                  {t("inventory.unitNumber")} *
                </Label>
                <Input
                  id="unit-number"
                  {...form.register("unit_number")}
                />
                {form.formState.errors.unit_number && (
                  <p className="text-sm text-destructive">
                    {t("common.required")}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label>{t("inventory.project")} *</Label>
                <Controller
                  control={form.control}
                  name="project_id"
                  render={({ field }) => (
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                    >
                      <SelectTrigger>
                        <SelectValue
                          placeholder={t("inventory.project")}
                        />
                      </SelectTrigger>
                      <SelectContent>
                        {projects.map((p) => (
                          <SelectItem key={p.id} value={p.id}>
                            {p.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
                {form.formState.errors.project_id && (
                  <p className="text-sm text-destructive">
                    {t("common.required")}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label>{t("inventory.propertyType")} *</Label>
                <Controller
                  control={form.control}
                  name="property_type"
                  render={({ field }) => (
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PROPERTY_TYPES.map((pt) => (
                          <SelectItem key={pt} value={pt}>
                            {t(`inventory.propertyTypes.${pt}`)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="unit-price">{t("inventory.price")} *</Label>
                <Input
                  id="unit-price"
                  type="number"
                  {...form.register("price")}
                />
                {form.formState.errors.price && (
                  <p className="text-sm text-destructive">
                    {t("common.required")}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="unit-area">{t("inventory.area")} *</Label>
                <Input
                  id="unit-area"
                  type="number"
                  {...form.register("area_sqm")}
                />
                {form.formState.errors.area_sqm && (
                  <p className="text-sm text-destructive">
                    {t("common.required")}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="unit-bedrooms">
                  {t("inventory.bedrooms")} *
                </Label>
                <Input
                  id="unit-bedrooms"
                  type="number"
                  {...form.register("bedrooms")}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="unit-bathrooms">
                  {t("inventory.bathrooms")} *
                </Label>
                <Input
                  id="unit-bathrooms"
                  type="number"
                  {...form.register("bathrooms")}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="unit-floor">{t("inventory.floor")}</Label>
                <Input
                  id="unit-floor"
                  type="number"
                  {...form.register("floor")}
                />
              </div>

              <div className="space-y-2">
                <Label>{t("inventory.finishing")} *</Label>
                <Controller
                  control={form.control}
                  name="finishing"
                  render={({ field }) => (
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {FINISHING_TYPES.map((ft) => (
                          <SelectItem key={ft} value={ft}>
                            {t(`inventory.finishingTypes.${ft}`)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>

              <div className="space-y-2">
                <Label>{t("common.status")} *</Label>
                <Controller
                  control={form.control}
                  name="status"
                  render={({ field }) => (
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {UNIT_STATUSES.map((s) => (
                          <SelectItem key={s} value={s}>
                            {t(`inventory.unitStatuses.${s}`)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit-notes">{t("inventory.notes")}</Label>
              <Input id="unit-notes" {...form.register("notes")} />
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
