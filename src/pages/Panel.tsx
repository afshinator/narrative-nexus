import { Switch } from "@/components/ui/switch";
import {
  DEFAULT_SOURCES,
  getSourcesByRegion,
  getSourcesByTier,
  REGION_LABELS,
  REGION_ORDER,
  type Source,
} from "../data/sources";
import { useStore } from "../store";

const TIERS = [1, 2, 3, 4, 5] as const;

const TIER_LABELS: Record<number, string> = {
  1: "Wire / Consensus Anchor",
  2: "Mainstream Editorial",
  3: "International",
  4: "Independent / Investigative",
  5: "Contrarian",
};

const TIER_COLORS: Record<number, string> = {
  1: "var(--nn-navy)",
  2: "var(--nn-navy)",
  3: "var(--nn-teal)",
  4: "var(--nn-slate)",
  5: "var(--nn-red)",
};

const REGION_COLORS: Record<string, string> = {
  na: "var(--nn-navy)",
  eu: "var(--nn-teal)",
  me: "var(--nn-amber)",
  asia: "var(--nn-red)",
  africa: "var(--nn-slate)",
  latam: "var(--nn-amber)",
  sa: "var(--nn-red)",
};

/** Pure: counts how many sources in a tier are active. */
function getActiveCount(activeIds: string[], tierSources: Source[]): number {
  return tierSources.filter((s) => activeIds.includes(s.id)).length;
}

export default function PanelPage() {
  const activeSources = useStore((s) => s.activeSources);
  const toggleSource = useStore((s) => s.toggleSource);
  const byTier = getSourcesByTier();
  const byRegion = getSourcesByRegion(DEFAULT_SOURCES, activeSources);

  const totalActive = activeSources.length;
  const totalAll = DEFAULT_SOURCES.length;
  const showLowWarning = totalActive < 12;

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

        {/* Tier distribution bar */}
        <div className="mb-4">
          <div className="flex h-2 overflow-hidden rounded-full bg-[var(--nn-surface2)]">
            {TIERS.map((tier) => {
              const count = getActiveCount(
                activeSources,
                byTier[String(tier)] ?? [],
              );
              const pct = (count / totalAll) * 100;
              if (pct <= 0) return null;
              return (
                <span
                  key={tier}
                  className="block h-full transition-all"
                  style={{
                    width: `${pct}%`,
                    backgroundColor: TIER_COLORS[tier],
                  }}
                />
              );
            })}
          </div>
          <div className="mt-1.5 flex items-center justify-between font-mono text-[0.7rem] uppercase tracking-[0.06em] text-[var(--nn-text-dim)]">
            <div className="flex gap-4">
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
            <span>
              {totalActive}/{totalAll} active
            </span>
          </div>
        </div>

        {/* Geographic breakdown row */}
        <div className="mb-4">
          <div className="mb-2 flex items-center gap-2">
            <span className="h-px flex-1 bg-[var(--nn-border)]" />
            <span className="font-mono text-[0.65rem] uppercase tracking-[0.08em] text-[var(--nn-text-dim)]">
              Geographic spread
            </span>
            <span className="h-px flex-1 bg-[var(--nn-border)]" />
          </div>
          {REGION_ORDER.map((region) => {
            const count = byRegion[region]?.length ?? 0;
            const pct = totalActive > 0 ? (count / totalActive) * 100 : 0;
            return (
              <div key={region} className="mb-1 flex items-center gap-2 last:mb-0">
                <span className="w-20 text-right font-mono text-[0.7rem] text-[var(--nn-text-dim)]">
                  {REGION_LABELS[region]}
                </span>
                <div className="flex h-2.5 flex-1 overflow-hidden rounded-full bg-[var(--nn-surface2)]">
                  {count > 0 && (
                    <span
                      className="block h-full rounded-full transition-all"
                      style={{
                        width: `${Math.max(pct, 4)}%`,
                        backgroundColor: REGION_COLORS[region],
                      }}
                    />
                  )}
                </div>
                <span className="w-6 text-right font-mono text-[0.7rem] tabular-nums text-[var(--nn-text-dim)]">
                  {count}
                </span>
              </div>
            );
          })}
        </div>

        {/* Low-panel warning */}
        {showLowWarning && (
          <div className="mb-4 rounded-md border border-[var(--nn-amber)] bg-[var(--nn-amber)]/10 px-3 py-2 font-sans text-[0.78rem] text-[var(--nn-amber)]">
            Panel size ({totalActive}) is below 12 sources. Consensus baseline
            reliability may be affected with fewer sources in the pool.
          </div>
        )}

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
