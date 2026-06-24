import { useStore } from "../store";
import { DEFAULT_SOURCES, getSourcesByTier, type Source } from "../data/sources";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";

const TIERS = [1, 2, 3, 4, 5] as const;

const TIER_LABELS: Record<number, string> = {
  1: "Wire / Consensus Anchor",
  2: "Mainstream Editorial",
  3: "International",
  4: "Independent / Investigative",
  5: "Contrarian",
};

/** Pure: counts how many sources in a tier are active. */
function getActiveCount(activeIds: string[], tierSources: Source[]): number {
  return tierSources.filter((s) => activeIds.includes(s.id)).length;
}

export default function PanelPage() {
  const activeSources = useStore((s) => s.activeSources);
  const toggleSource = useStore((s) => s.toggleSource);
  const byTier = getSourcesByTier();

  const totalActive = activeSources.length;
  const totalAll = DEFAULT_SOURCES.length;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
        Panel Management
      </h1>

      {/* Category Balance Indicator */}
      <Card className="p-4">
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">
          Balance
        </h2>
        <div className="flex items-center gap-2">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
            {TIERS.map((tier) => {
              const count = getActiveCount(
                activeSources,
                byTier[String(tier)] ?? [],
              );
              const pct = (count / totalAll) * 100;
              return (
                <span
                  key={tier}
                  className="inline-block h-full"
                  style={{
                    width: `${pct}%`,
                    backgroundColor:
                      tier <= 2
                        ? "var(--nn-green)"
                        : tier === 3
                          ? "var(--nn-amber)"
                          : tier === 4
                            ? "var(--nn-neutral)"
                            : "var(--nn-red)",
                  }}
                />
              );
            })}
          </div>
          <span className="font-mono text-xs tabular-nums text-muted-foreground">
            {totalActive}/{totalAll}
          </span>
        </div>
        <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
          {TIERS.map((tier) => {
            const tierSources = byTier[String(tier)] ?? [];
            const active = getActiveCount(activeSources, tierSources);
            return (
              <span key={tier}>
                T{tier}: {active}/{tierSources.length}
              </span>
            );
          })}
        </div>
      </Card>

      {/* Source List by Tier */}
      {TIERS.map((tier) => {
        const tierSources = byTier[String(tier)] ?? [];
        return (
          <Card key={tier} className="p-4">
            <h2 className="mb-1 text-sm font-medium text-foreground">
              Tier {tier}
            </h2>
            <p className="mb-3 text-xs text-muted-foreground">
              {TIER_LABELS[tier]}
              {tier <= 2 && " — consensus pool"}
            </p>
            <div className="space-y-2">
              {tierSources.map((source) => (
                <div
                  key={source.id}
                  className="flex items-center justify-between rounded-md px-3 py-2 transition-colors hover:bg-muted/50"
                >
                  <div>
                    <span className="text-sm text-foreground">
                      {source.name}
                    </span>
                    <span className="ml-2 font-mono text-xs text-muted-foreground">
                      {source.domain}
                    </span>
                  </div>
                  <Switch
                    checked={activeSources.includes(source.id)}
                    onCheckedChange={() => toggleSource(source.id)}
                    aria-label={`Toggle ${source.name}`}
                  />
                </div>
              ))}
            </div>
          </Card>
        );
      })}
    </div>
  );
}
