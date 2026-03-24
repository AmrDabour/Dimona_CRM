import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { usePipelineStats, useLeadsByStage } from "@/services/pipelineService";
import { useUpdateLeadStatus } from "@/services/leadService";
import type { Lead, LeadStatus } from "@/types/lead";
import { cn, formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChevronDown, Phone, User, Calendar } from "lucide-react";

const STAGES: LeadStatus[] = [
  "new",
  "contacted",
  "viewing",
  "negotiation",
  "won",
  "lost",
];

const STAGE_COLORS: Record<LeadStatus, { bg: string; border: string; dot: string }> = {
  new:         { bg: "bg-blue-50 dark:bg-blue-950/30",   border: "border-blue-300 dark:border-blue-700",   dot: "bg-blue-500" },
  contacted:   { bg: "bg-yellow-50 dark:bg-yellow-950/30", border: "border-yellow-300 dark:border-yellow-700", dot: "bg-yellow-500" },
  viewing:     { bg: "bg-purple-50 dark:bg-purple-950/30", border: "border-purple-300 dark:border-purple-700", dot: "bg-purple-500" },
  negotiation: { bg: "bg-orange-50 dark:bg-orange-950/30", border: "border-orange-300 dark:border-orange-700", dot: "bg-orange-500" },
  won:         { bg: "bg-green-50 dark:bg-green-950/30",  border: "border-green-300 dark:border-green-700",  dot: "bg-green-500" },
  lost:        { bg: "bg-red-50 dark:bg-red-950/30",     border: "border-red-300 dark:border-red-700",     dot: "bg-red-500" },
};

function StageColumn({ status }: { status: LeadStatus }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data: leadsData, isLoading } = useLeadsByStage(status);
  const leads = leadsData?.items || [];
  const { data: stats } = usePipelineStats();
  const updateStatus = useUpdateLeadStatus();

  const colors = STAGE_COLORS[status];
  const count = stats?.stages.find((s) => s.stage === status)?.count ?? leads?.length ?? 0;

  function handleStatusChange(lead: Lead, newStatus: LeadStatus) {
    if (newStatus === lead.status) return;
    updateStatus.mutate({ id: lead.id, data: { status: newStatus } });
  }

  return (
    <div
      className={cn(
        "flex h-full w-72 shrink-0 flex-col rounded-xl border-2",
        colors.bg,
        colors.border,
      )}
    >
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <span className={cn("h-2.5 w-2.5 rounded-full", colors.dot)} />
        <h3 className="text-sm font-semibold">
          {t(`leads.statuses.${status}`, status)}
        </h3>
        <Badge variant="secondary" className="ms-auto text-xs">
          {count}
        </Badge>
      </div>

      <ScrollArea className="flex-1 p-2">
        <div className="flex flex-col gap-2">
          {isLoading &&
            Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-lg" />
            ))}

          {!isLoading && leads?.length === 0 && (
            <p className="py-8 text-center text-xs text-muted-foreground">
              {t("common.noData")}
            </p>
          )}

          {leads?.map((lead) => (
            <Card
              key={lead.id}
              className="cursor-pointer p-3 transition-shadow hover:shadow-md"
              onClick={() => navigate(`/leads/${lead.id}`)}
            >
              <div className="flex items-start justify-between gap-1">
                <p className="text-sm font-medium leading-tight">
                  {lead.full_name}
                </p>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 shrink-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <ChevronDown className="h-3.5 w-3.5" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent
                    align="end"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {STAGES.filter((s) => s !== status).map((s) => (
                      <DropdownMenuItem
                        key={s}
                        onClick={() => handleStatusChange(lead, s)}
                      >
                        <span
                          className={cn(
                            "me-2 inline-block h-2 w-2 rounded-full",
                            STAGE_COLORS[s].dot,
                          )}
                        />
                        {t(`leads.statuses.${s}`, s)}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              <div className="mt-2 space-y-1">
                {lead.phone && (
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Phone className="h-3 w-3" />
                    <span dir="ltr">{lead.phone}</span>
                  </div>
                )}
                {lead.assigned_user && (
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <User className="h-3 w-3" />
                    <span>{lead.assigned_user.full_name}</span>
                  </div>
                )}
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3" />
                  <span>{formatDate(lead.created_at)}</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

function PipelineSkeleton() {
  return (
    <div className="flex gap-4 overflow-hidden p-6">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-[500px] w-72 shrink-0 rounded-xl" />
      ))}
    </div>
  );
}

export default function PipelinePage() {
  const { t } = useTranslation();
  const { isLoading } = usePipelineStats();

  if (isLoading) return <PipelineSkeleton />;

  return (
    <div className="flex h-full flex-col">
      <div className="shrink-0 px-6 pt-6 pb-2">
        <h1 className="text-2xl font-bold tracking-tight">
          {t("pipeline.title")}
        </h1>
      </div>

      <div className="flex-1 overflow-x-auto overflow-y-hidden px-6 pb-6">
        <div className="flex h-full gap-4">
          {STAGES.map((status) => (
            <StageColumn key={status} status={status} />
          ))}
        </div>
      </div>
    </div>
  );
}
