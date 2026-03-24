const fs = require('fs');
const path = 'frontend/src/pages/reports/AgentPerformancePage.tsx';
let code = fs.readFileSync(path, 'utf8');

const startMarker = '{/* ── Points Summary ─────────────────────────────────────────── */}';
const endMarker = '{/* Pipeline chart */}';

if (code.includes(startMarker) && code.includes(endMarker)) {
  const before = code.substring(0, code.indexOf(startMarker));
  const after = code.substring(code.indexOf(endMarker));

  const newMiddle = `{/* ── Points Summary ─────────────────────────────────────────── */}
      {activePoints && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Star className="h-5 w-5 text-yellow-400" />
              {t("reports.pointsSummary", "Points Summary")}
            </CardTitle>
            <div className={\`flex items-center gap-1.5 text-sm font-semibold \${tierColor}\`}>
              <Medal className="h-4 w-4" />
              {t(\`gamification.\${tierName}\`, tierName)}
              {activePoints.rank > 0 && (
                <span className="ms-2 font-normal text-muted-foreground">
                  #{activePoints.rank}
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <p className="text-4xl font-bold">{activePoints.total_points}</p>
              <p className="text-sm text-muted-foreground">
                {t("gamification.totalPoints")}
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-4">
              {pointCategories.map((cat) => (
                <div key={cat.label} className="flex items-center gap-3 rounded-lg border p-3">
                  <div className={\`h-3 w-3 rounded-full \${cat.color}\`} />
                  <div>
                    <p className="text-lg font-bold">{cat.value}</p>
                    <p className="text-xs text-muted-foreground">{cat.label}</p>
                  </div>
                </div>
              ))}
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => setIsModalOpen(true)}
            >
              <Star className="me-2 h-4 w-4" />
              {t("gamification.pointsBreakdown")}
            </Button>
          </CardContent>
          <AgentPointsBreakdownModal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            pointHistory={activePointHistory}
            agentName={performance?.agent?.name}
          />
        </Card>
      )}

      `;

  fs.writeFileSync(path, before + newMiddle + after);
  console.log('Replaced successfully');
} else {
  console.log('Markers not found');
}
