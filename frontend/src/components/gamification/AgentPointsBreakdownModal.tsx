import { useTranslation } from "react-i18next";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { usePointRules } from "@/services/gamificationService";
import type { PointTransactionPage } from "@/types/gamification";
import {
  History,
  Info,
  ArrowUpCircle,
  ArrowDownCircle,
  Medal,
} from "lucide-react";
import { format } from "date-fns";
import { arSA, enUS } from "date-fns/locale";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  pointHistory?: PointTransactionPage;
  agentName?: string;
}

export function AgentPointsBreakdownModal({
  isOpen,
  onClose,
  pointHistory,
  agentName,
}: Props) {
  const { t, i18n } = useTranslation();
  const { data: rulesData, isLoading: isLoadingRules } = usePointRules();

  const isRTL = i18n.dir() === "rtl";
  const locale = isRTL ? arSA : enUS;

  const pointRules = rulesData?.point_rules?.filter((r) => r.is_active) ?? [];
  const penaltyRules =
    rulesData?.penalty_rules?.filter((r) => r.is_active) ?? [];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[700px] max-h-[85vh] flex flex-col p-0">
        <DialogHeader className="p-6 pb-2">
          <DialogTitle className="flex items-center gap-2 text-xl">
            <Medal className="h-6 w-6 text-yellow-500" />
            {t("gamification.pointsBreakdown")}
            {agentName && (
              <span className="text-muted-foreground text-sm font-normal ms-2">
                — {agentName}
              </span>
            )}
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="history" className="flex flex-col flex-1 mx-6 mb-6">
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="history" className="flex items-center gap-2">
              <History className="h-4 w-4" />
              {t("gamification.history")}
            </TabsTrigger>
            <TabsTrigger value="rules" className="flex items-center gap-2">
              <Info className="h-4 w-4" />
              {t("gamification.howToEarn")}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="history" className="flex-1 mt-0">
            <ScrollArea className="h-[400px] w-full rounded-md border p-4">
              {!pointHistory || pointHistory.items.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
                  <History className="h-10 w-10 mb-2 opacity-50" />
                  <p>{t("gamification.noHistory")}</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {pointHistory.items.map((txn) => {
                    const isPositive = txn.points > 0;
                    return (
                      <div
                        key={txn.id}
                        className="flex items-center justify-between border-b pb-3 last:border-0 last:pb-0"
                      >
                        <div className="flex flex-col">
                          <span className="font-semibold text-sm">
                            {t(`gamification.events.${txn.event_type}`, txn.event_type)}
                          </span>
                          <span className="text-xs text-muted-foreground mt-0.5">
                            {format(new Date(txn.created_at), "PP p", {
                              locale,
                            })}
                          </span>
                          {txn.note && (
                            <span className="text-xs text-muted-foreground mt-1">
                              {txn.note}
                            </span>
                          )}
                        </div>
                        <div
                          className={`flex items-center gap-1 font-bold ${
                            isPositive ? "text-green-600" : "text-red-500"
                          }`}
                        >
                          {isPositive ? (
                            <ArrowUpCircle className="h-4 w-4" />
                          ) : (
                            <ArrowDownCircle className="h-4 w-4" />
                          )}
                          {isPositive ? "+" : ""}
                          {txn.points}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </ScrollArea>
          </TabsContent>

          <TabsContent value="rules" className="flex-1 mt-0">
            <ScrollArea className="h-[400px] w-full rounded-md border p-4">
              {isLoadingRules ? (
                <div className="flex h-full items-center justify-center">
                  <span className="loading loading-spinner" />
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Positive Points */}
                  <div>
                    <h3 className="font-bold text-lg mb-3 flex items-center gap-2 text-green-600">
                      <ArrowUpCircle className="h-5 w-5" />
                      {t("gamification.pointRules")}
                    </h3>
                    {pointRules.length === 0 ? (
                      <p className="text-sm text-muted-foreground">
                        {t("gamification.noRules")}
                      </p>
                    ) : (
                      <div className="grid gap-3 sm:grid-cols-2">
                        {pointRules.map((rule) => (
                          <div
                            key={rule.id}
                            className="flex flex-col p-3 border rounded-lg bg-green-50/50 dark:bg-green-950/10"
                          >
                            <div className="flex justify-between items-start mb-1">
                              <span className="font-semibold text-sm">
                                {t(`gamification.events.${rule.event_type}`, rule.event_type)}
                              </span>
                              <span className="font-bold text-green-600 bg-green-100 dark:bg-green-900 px-2 py-0.5 rounded text-xs">
                                +{rule.points} {t("gamification.pointsPerEvent")}
                              </span>
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {rule.description}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Negative Penalties */}
                  <div>
                    <h3 className="font-bold text-lg mb-3 flex items-center gap-2 text-red-500 mt-6 pt-4 border-t">
                      <ArrowDownCircle className="h-5 w-5" />
                      {t("gamification.penaltyRules")}
                    </h3>
                    {penaltyRules.length === 0 ? (
                      <p className="text-sm text-muted-foreground">
                        {t("gamification.noRules")}
                      </p>
                    ) : (
                      <div className="grid gap-3 sm:grid-cols-2">
                        {penaltyRules.map((rule) => (
                          <div
                            key={rule.id}
                            className="flex flex-col p-3 border rounded-lg bg-red-50/50 dark:bg-red-950/10"
                          >
                            <div className="flex justify-between items-start mb-1">
                              <span className="font-semibold text-sm">
                                {t(`gamification.events.${rule.event_type}`, rule.event_type)}
                              </span>
                              <span className="font-bold text-red-500 bg-red-100 dark:bg-red-900 px-2 py-0.5 rounded text-xs">
                                {rule.points} {t("gamification.pointsPerEvent")}
                              </span>
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              {rule.description}
                              {rule.threshold_minutes !== null && (
                                <div className="mt-1 font-medium text-red-600/80">
                                  {t("common.after", "After")} {rule.threshold_minutes} {t("gamification.minutes")}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
