import { useStore } from "../store";
import { DEFAULT_SOURCES, getSourcesByTier, type Source } from "../data/sources";
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
    <div className="mx-auto max-w-[1340px] space-y-6">
      {/* Page header — mock style */}
      <div className="flex items-center gap-3">
        <h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
          Panel Management
        </h1>
      </div>
      <p className="-mt-4 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
        Activate and deactivate sources in the tracked panel
      </p>

      {/* Single card containing everything */}
      <div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6">
        {/* Category Balance Indicator */}
        <h2 className="mb-3 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
          Category Balance
        </h2>
        <div className="mb-4 flex items-center gap-2">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--nn-surface2)]">
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
                        ? "var(--nn-navy)"
                        : tier === 3
                          ? "var(--nn-teal)"
                          : tier === 4
                            ? "var(--nn-slate)"
                            : "var(--nn-red)",
                  }}
                />
              );
            })}
          </div>
          <span className="font-mono text-xs tabular-nums text-[var(--nn-text-dim)]">
            {totalActive}/{totalAll}
          </span>
        </div>
        <div className="mb-6 flex gap-6 font-mono text-[0.7rem] uppercase tracking-[0.06em] text-[var(--nn-text-dim)]">
          {TIERS.map((tier) => {
            const tierSources = byTier[String(tier)] ?? [];
            const active = getActiveCount(activeSources, tierSources);
            return (
              <span key={tier} className="font-bold">
                T{tier}: {active}/{tierSources.length}
              </span>
            );
          })}
        </div>

        {/* Source List by Tier */}
        {TIERS.map((tier) => {
          const tierSources = byTier[String(tier)] ?? [];
          const isConsensus = tier <= 2;
          return (
            <div key={tier} className="mb-4 last:mb-0">
              <div className="mb-2 flex items-baseline gap-2">
                <h3 className="font-heading text-[0.84rem] font-semibold text-[var(--nn-text)]">
                  Tier {tier}
                </h3>
                <span className="font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
                  {TIER_LABELS[tier]}
                  {isConsensus && " — consensus pool"}
                </span>
              </div>
              <div className="space-y-px">
                {tierSources.map((source) => (
                  <div
                    key={source.id}
                    className="flex items-center justify-between rounded px-3 py-2 transition-colors hover:bg-[var(--nn-surface2)]"
                  >
                    <div>
                      <span className="text-[0.9rem] font-semibold text-[var(--nn-text)]">
                        {source.name}
                      </span>
                      <span className="ml-2.5 font-mono text-[0.78rem] text-[var(--nn-text-dim)]">
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
              {tier < 5 && <hr className="mt-4 border-[var(--nn-border)]" />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
