import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/stores/authStore";
import { useLeaderboard } from "@/services/gamificationService";
import { useTeams } from "@/services/teamService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Trophy, Medal, Award, Star, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LeaderboardEntry } from "@/types/gamification";

const TIER_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  gold: {
    bg: "bg-amber-100 dark:bg-amber-900/30",
    text: "text-amber-700 dark:text-amber-300",
    border: "border-amber-300 dark:border-amber-700",
  },
  silver: {
    bg: "bg-slate-100 dark:bg-slate-800/50",
    text: "text-slate-600 dark:text-slate-300",
    border: "border-slate-300 dark:border-slate-600",
  },
  bronze: {
    bg: "bg-orange-100 dark:bg-orange-900/30",
    text: "text-orange-700 dark:text-orange-300",
    border: "border-orange-300 dark:border-orange-700",
  },
};

function TierBadge({ name }: { name: string }) {
  const { t } = useTranslation();
  const style = TIER_STYLES[name] ?? TIER_STYLES.bronze;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold capitalize",
        style.bg,
        style.text,
        style.border,
      )}
    >
      <Star className="h-3 w-3" />
      {t(`gamification.${name}`, name)}
    </span>
  );
}

function PodiumCard({
  entry,
  place,
  isCurrentUser,
}: {
  entry: LeaderboardEntry;
  place: 1 | 2 | 3;
  isCurrentUser: boolean;
}) {
  const { t } = useTranslation();
  const icons = { 1: Trophy, 2: Medal, 3: Award };
  const Icon = icons[place];
  const heights = { 1: "h-40", 2: "h-32", 3: "h-28" };
  const iconColors = {
    1: "text-amber-500",
    2: "text-slate-400",
    3: "text-orange-500",
  };

  return (
    <Card
      className={cn(
        "flex flex-col items-center justify-end text-center transition-all",
        heights[place],
        isCurrentUser && "ring-2 ring-primary",
      )}
    >
      <CardContent className="flex flex-col items-center gap-1 p-4">
        <Icon className={cn("h-7 w-7", iconColors[place])} />
        <p className="text-sm font-bold text-center px-1 line-clamp-2 min-h-[2.5em]">{entry.full_name}</p>
        <p className="text-lg font-black">{entry.total_points}</p>
        <TierBadge name={entry.tier.name} />
      </CardContent>
    </Card>
  );
}

function getMonthOptions(): { value: string; label: string }[] {
  const options: { value: string; label: string }[] = [];
  const now = new Date();
  for (let i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    const label = d.toLocaleDateString("en-US", { month: "long", year: "numeric" });
    options.push({ value, label });
  }
  return options;
}

export default function LeaderboardPage() {
  const { t } = useTranslation();
  const currentUser = useAuthStore((s) => s.user);
  const monthOptions = useMemo(getMonthOptions, []);

  const [month, setMonth] = useState<string | undefined>(undefined);
  const [teamId, setTeamId] = useState<string | undefined>(undefined);

  const { data: entries, isLoading } = useLeaderboard(month, teamId);
  const { data: teams } = useTeams();

  const top3 = entries?.slice(0, 3) ?? [];
  const rest = entries?.slice(3) ?? [];

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Trophy className="h-6 w-6 text-amber-500" />
            {t("gamification.leaderboard")}
          </h1>
          <p className="text-muted-foreground">
            {t("gamification.leaderboardSubtitle")}
          </p>
        </div>

        <div className="flex gap-2">
          <Select value={month ?? "current"} onValueChange={(v) => setMonth(v === "current" ? undefined : v)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder={t("gamification.currentMonth")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="current">{t("gamification.currentMonth")}</SelectItem>
              {monthOptions.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={teamId ?? "all"} onValueChange={(v) => setTeamId(v === "all" ? undefined : v)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder={t("gamification.allTeams")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("gamification.allTeams")}</SelectItem>
              {teams?.map((team) => (
                <SelectItem key={team.id} value={team.id}>
                  {team.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-40 rounded-xl" />
            ))}
          </div>
          <Skeleton className="h-[300px] rounded-xl" />
        </div>
      ) : entries && entries.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Trophy className="mx-auto h-12 w-12 text-muted-foreground/40" />
            <p className="mt-4 text-muted-foreground">{t("gamification.noDataYet")}</p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Podium: top 3 */}
          {top3.length > 0 && (
            <div className="grid grid-cols-3 items-end gap-4">
              {top3[1] && (
                <PodiumCard
                  entry={top3[1]}
                  place={2}
                  isCurrentUser={top3[1].user_id === currentUser?.id}
                />
              )}
              {top3[0] && (
                <PodiumCard
                  entry={top3[0]}
                  place={1}
                  isCurrentUser={top3[0].user_id === currentUser?.id}
                />
              )}
              {top3[2] && (
                <PodiumCard
                  entry={top3[2]}
                  place={3}
                  isCurrentUser={top3[2].user_id === currentUser?.id}
                />
              )}
            </div>
          )}

          {/* Rest of leaderboard */}
          {rest.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  {t("gamification.rankings")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="divide-y">
                  {rest.map((entry) => {
                    const isCurrent = entry.user_id === currentUser?.id;
                    return (
                      <div
                        key={entry.user_id}
                        className={cn(
                          "flex items-center gap-4 py-3",
                          isCurrent && "rounded-lg bg-primary/5 px-3",
                        )}
                      >
                        <span className="w-8 text-center text-lg font-bold text-muted-foreground">
                          {entry.rank}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{entry.full_name}</p>
                          <p className="text-xs text-muted-foreground">{entry.email}</p>
                        </div>
                        <div className="hidden sm:flex gap-3 text-xs text-muted-foreground">
                          <span title={t("gamification.activityPts")}>
                            {t("gamification.activityShort")}: {entry.activity_points}
                          </span>
                          <span title={t("gamification.compliancePts")}>
                            {t("gamification.complianceShort")}: {entry.compliance_points}
                          </span>
                          <span title={t("gamification.conversionPts")}>
                            {t("gamification.conversionShort")}: {entry.conversion_points}
                          </span>
                        </div>
                        <TierBadge name={entry.tier.name} />
                        <span className="w-16 text-end text-lg font-bold">
                          {entry.total_points}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
