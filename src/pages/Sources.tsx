import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import ArchetypePills from "../components/ArchetypePills";
import LensToggle from "../components/LensToggle";
import ScatterPlot from "../components/ScatterPlot";
import type { ReputationScore } from "../data/scores";
import { DEFAULT_SOURCES } from "../data/sources";
import { useStore } from "../store";
import { getArchetype } from "../utils/archetype";

// ponytail: domain→slug map for API score lookups. API returns domains
// ("reuters.com") but DEFAULT_SOURCES uses slugs ("reuters").
const _domainToSlug = new Map(
  DEFAULT_SOURCES.map((s) => [s.domain, s.id] as const),
);

interface Props {
  scores?: ReputationScore[];
}

const SCORE_COLUMNS = [
  { key: "R_orig", label: "Origination", direction: null },
  { key: "R_val", label: "Validation", direction: "higher" },
  { key: "R_speed", label: "Speed Premium", direction: "lower" },
  { key: "R_frame", label: "Framing Consist.", direction: "lower" },
  { key: "R_edit", label: "Silent Edits", direction: "lower" },
  { key: "R_correct", label: "Corrections", direction: null },
] as const;

type SortKey = "name" | (typeof SCORE_COLUMNS)[number]["key"];

function PageHeader({ sourceCount }: { sourceCount: number }) {
  return (
    <div className="-mx-8 -mt-7 mb-6 border-b border-(--nn-border) bg-(--nn-surface) px-8 py-6">
      <div className="mx-auto flex w-full max-w-[1340px] flex-col gap-8 md:flex-row md:items-center">
        <p className="flex-1 font-heading text-[1.35rem] font-semibold leading-tight text-(--nn-navy)">
          We can't extract truth,
          <br />
          but we can identify consensus reality
        </p>

        {/* Vertical divider: hidden on mobile, visible on medium+ screens */}
        <div className="hidden w-px self-stretch bg-(--nn-border) md:block"></div>

        <p className="flex-1 font-sans text-[0.95rem] leading-relaxed text-(--nn-text-dim)">
          Narrative Nexus tracks how (currently) {sourceCount} outlets originate
          and validate claims — scoring each source 0–100 across six reputation
          dimensions.
        </p>
        <p className="flex-1 font-sans text-[0.95rem] leading-relaxed text-(--nn-text-dim)">
          Click any dot or table row (in ledger below) to open that outlet's
          full profile.
        </p>
      </div>
    </div>
  );
}

function AboutValidationCard() {
  return (
    <div className="rounded-xl border border-(--nn-border) bg-(--nn-surface) p-5 shadow-xs">
      <h2 className="font-heading text-[1.1rem] font-bold text-(--nn-navy) mb-2">
        About Validation Scoring
      </h2>
      <p className="font-sans text-[0.85rem] leading-relaxed text-(--nn-text-dim)">
        Validation tracks how rigorously an outlet verifies a claim before
        publishing. High scores indicate primary source confirmation, zero
        stealth edits, and rapid, transparent corrections. Low scores reflect
        unmitigated aggregation of unverified third-party reporting.
      </p>
    </div>
  );
}

const DEMO_STORIES = [
  { id: 966, title: "US-Iran War: March Escalation & April Ceasefire" },
  { id: 924, title: "Venezuela Emergency and Rescue Response" },
] as const;

function DemoCorpusNote() {
  return (
    <aside
      aria-label="About this data"
      className="max-w-[420px] rounded-lg border border-[color-mix(in_srgb,var(--nn-amber)_35%,transparent)] bg-[color-mix(in_srgb,var(--nn-amber)_8%,transparent)] px-4 py-3"
    >
      <div className="mb-1.5 font-mono text-[0.75rem] font-medium tracking-[0.06em] text-[var(--nn-amber)]">
        ABOUT THIS DATA
      </div>
      <p className="mb-2 font-sans text-[0.82rem] leading-normal text-[var(--nn-text)]">
        358 articles from 37 sources, processed through the full pipeline —
        378 claims, 10 cross-source absorptions across 17 story clusters.
      </p>
      <p className="font-sans text-[0.82rem] leading-normal text-[var(--nn-text-dim)]">
        Two stories traced end-to-end:
      </p>
      <ul className="mt-0.5 space-y-0.5">
        {DEMO_STORIES.map((story) => (
          <li key={story.id}>
            <Link
              to={`/cluster/${story.id}`}
              className="font-sans text-[0.82rem] font-medium text-[var(--nn-navy)] hover:underline"
            >
              {story.title}
            </Link>
          </li>
        ))}
      </ul>
    </aside>
  );
}

function Legend() {
  return (
    <div className="mb-3 space-y-1.5 font-sans text-[0.85rem] text-(--nn-text)">
      <p>
        Each source scored 0–100 across six reputation dimensions.
      </p>
      <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
        <span className="font-semibold">Origination</span>
        <span className="text-(--nn-text-dim)">
          first to report a story that becomes consensus-absorbed
        </span>
        <span className="font-semibold">Validation</span>
        <span className="text-(--nn-text-dim)">
          claims absorbed by the panel consensus
        </span>
        <span className="font-semibold">Speed</span>
        <span className="text-(--nn-text-dim)">
          how quickly claims spread (lower is faster)
        </span>
        <span className="font-semibold">Framing</span>
        <span className="text-(--nn-text-dim)">
          consistency of editorial framing across stories
        </span>
        <span className="font-semibold">Silent Edits</span>
        <span className="text-(--nn-text-dim)">
          rate of unreported article changes
        </span>
        <span className="font-semibold">Corrections</span>
        <span className="text-(--nn-text-dim)">
          rate of formal published corrections
        </span>
      </div>
      <p className="text-(--nn-text-dim)">
        * Not yet computed — shows "—" for all sources. Sources with 0
        Validation have no consensus-absorbed claims yet.
      </p>
    </div>
  );
}

export default function SourcesPage({ scores: propScores }: Props) {
  const navigate = useNavigate();
  const [hoveredSource, setHoveredSource] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(
    null,
  );
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDir, setSortDir] = useState<1 | -1>(1);
  const [fetchedScores, setFetchedScores] = useState<ReputationScore[]>([]);
  const [dateRange, setDateRange] = useState<{
    min: string;
    max: string;
  } | null>(null);

  // T2b: Lens toggle — persisted in URL search params for deep-linking
  const [searchParams, setSearchParams] = useSearchParams();
  const lensParam = searchParams.get("lens");
  const lens: "consensus" | "coverage" =
    lensParam === "coverage" ? "coverage" : "consensus";
  const setLens = useCallback(
    (l: "consensus" | "coverage") => {
      setSearchParams(l === "coverage" ? { lens: "coverage" } : {});
    },
    [setSearchParams],
  );

  // Coverage landscape data (fetched once, pan-vertical)
  interface CoverageSource {
    source_id: number;
    name: string;
    tier: number;
    total_claims: number;
    solo_claims: number;
    solo_share_pct: number;
    has_absorbed_claims: number;
  }
  const [coverageData, setCoverageData] = useState<CoverageSource[]>([]);
  useEffect(() => {
    if (typeof window !== "undefined" && !window.fetch) return;
    fetch("/api/coverage-landscape")
      .then((r) => r.json())
      .then((data) => setCoverageData(data.sources ?? []))
      .catch(() => {});
  }, []);

  // T3: Transform coverage data for ScatterPlot (x=log10(claims), y=solo_share)
  // Build name→slug map once so coverage source IDs match DEFAULT_SOURCES slugs
  const nameToSlug = useMemo(() => {
    const map = new Map<string, string>();
    for (const src of DEFAULT_SOURCES) {
      map.set(src.name.toLowerCase(), src.id);
    }
    return map;
  }, []);

  const coverageScatter = useMemo(() => {
    return coverageData
      .filter((s) => s.total_claims > 0)
      .map((s) => ({
        sourceId: nameToSlug.get(s.name.toLowerCase()) ?? String(s.source_id),
        name: s.name,
        tier: s.tier,
        R_orig: Math.max(1, s.total_claims),
        R_val: s.solo_share_pct,
        archetype: null,
      }));
  }, [coverageData, nameToSlug]);

  // E2: day span for caption
  const daySpan = useMemo(() => {
    if (!dateRange) return null;
    const d1 = new Date(dateRange.min);
    const d2 = new Date(dateRange.max);
    const days = Math.ceil((d2.getTime() - d1.getTime()) / 86400000) + 1;
    return days;
  }, [dateRange]);

  const filter = useStore((s) => s.archetypeFilter);
  const activeSources = useStore((s) => s.activeSources);
  const visibleSources = useMemo(
    () => DEFAULT_SOURCES.filter((s) => activeSources.includes(s.id)),
    [activeSources],
  );

  // Fetch scores from API — prefers fetchedScores, falls back to propScores
  // ponytail: guard against missing fetch (jsdom test env)
  useEffect(() => {
    if (typeof window !== "undefined" && !window.fetch) return;
    let cancelled = false;
    setFetchedScores([]);
    setDateRange(null);
    fetch(`/api/scores?vertical=geopolitics`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load scores");
        return r.json();
      })
      .then((data) => {
        if (cancelled) return;
        const raw: ReputationScore[] = data.scores ?? [];
        const mapped = raw.map((s) => ({
          ...s,
          sourceId: _domainToSlug.get(s.sourceId) ?? s.sourceId,
        }));
        setFetchedScores(mapped);
        if (data.date_min && data.date_max) {
          setDateRange({ min: data.date_min, max: data.date_max });
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  // ponytail: useMemo prevents new [] reference on every render before fetch completes.
  // An unstable scores ref cascades into scoreMap → scatterData → D3 rebuild.
  const scores = useMemo(
    () => (fetchedScores.length > 0 ? fetchedScores : (propScores ?? [])),
    [fetchedScores, propScores],
  );

  const scoreMap = useMemo(
    () =>
      new Map(
        scores
          .filter((s) => s.vertical === "geopolitics")
          .map((s) => [s.sourceId, s]),
      ),
    [scores],
  );

  // Compute panel median for archetype assignment
  const panelMedian = useMemo(() => {
    if (scores.length === 0) return { orig: 50, val: 50 };
    const sorted = {
      orig: [...scores].sort((a, b) => a.R_orig - b.R_orig),
      val: [...scores].sort((a, b) => a.R_val - b.R_val),
    };
    const mid = Math.floor(scores.length / 2);
    return {
      orig:
        scores.length % 2
          ? sorted.orig[mid].R_orig
          : (sorted.orig[mid - 1].R_orig + sorted.orig[mid].R_orig) / 2,
      val:
        scores.length % 2
          ? sorted.val[mid].R_val
          : (sorted.val[mid - 1].R_val + sorted.val[mid].R_val) / 2,
    };
  }, [scores]);

  // Scatter plot data: enriched sources with scores and archetype for color encoding
  // A2: apply archetype filter — keep all points but dim non-matching
  const scatterData = useMemo(
    () =>
      visibleSources.map((source) => {
        const score = scoreMap.get(source.id);
        const archetype = score
          ? getArchetype(
              score.R_orig,
              score.R_val,
              panelMedian.orig,
              panelMedian.val,
            )
          : null;
        return {
          sourceId: source.id,
          name: source.name,
          tier: source.tier,
          R_orig: score?.R_orig ?? 0,
          R_val: score?.R_val ?? null,
          archetype,
        };
      }),
    [scoreMap, panelMedian, visibleSources, filter],
  );

  // F2c: Split scatter data into graded (has R_val) and ungraded (no R_val yet)
  // A2: When archetype filter is active, hide non-matching points from plot
  const scatterVisible = useMemo(
    () =>
      filter === null
        ? scatterData
        : scatterData.filter((s) => s.archetype === filter),
    [scatterData, filter],
  );
  const gradedData = useMemo(
    () =>
      scatterVisible.filter(
        (s): s is typeof s & { R_val: number } => s.R_val != null,
      ),
    [scatterVisible],
  );
  const ungradedSources = useMemo(
    () => scatterVisible.filter((s) => s.R_val == null),
    [scatterVisible],
  );

  // Enrich sources with scores + archetype, then filter + sort
  const rows = useMemo(() => {
    const enriched = visibleSources.map((source) => {
      const score = scoreMap.get(source.id);
      const archetype = score
        ? getArchetype(
            score.R_orig,
            score.R_val,
            panelMedian.orig,
            panelMedian.val,
          )
        : null;
      return { source, score, archetype };
    });

    // Filter by archetype — dim-mode: keep all rows, dim non-matching
    const allRows = enriched.map((r) => ({
      ...r,
      dimmed: filter !== null && r.archetype !== filter,
    }));

    // Sort
    allRows.sort((a, b) => {
      let va: number | string, vb: number | string;
      if (sortKey === "name") {
        va = a.source.name.toLowerCase();
        vb = b.source.name.toLowerCase();
      } else {
        va = a.score?.[sortKey] ?? 0;
        vb = b.score?.[sortKey] ?? 0;
      }
      if (va < vb) return -1 * sortDir;
      if (va > vb) return 1 * sortDir;
      return 0;
    });

    return allRows;
  }, [scoreMap, panelMedian, filter, sortKey, sortDir, visibleSources]);

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === 1 ? -1 : 1));
    } else {
      setSortKey(key);
      setSortDir(1);
    }
  }

  function sortArrow(key: SortKey) {
    if (sortKey !== key) return "";
    return sortDir === 1 ? " ↑" : " ↓";
  }

  const handleSelect = useCallback(
    (id: string) => {
      const source = DEFAULT_SOURCES.find((s) => s.id === id);
      if (source) navigate(`/source/${source.domain}`);
    },
    [navigate],
  );

  const handleHoverPosition = useCallback(
    (id: string | null, x: number, y: number) => {
      setHoveredSource(id);
      if (id) {
        setTooltipPos({ x, y });
      } else {
        setTooltipPos(null);
      }
    },
    [],
  );

  return (
    <>
      <PageHeader sourceCount={visibleSources.length} />

      <div className="mx-auto max-w-[1340px] space-y-6">
        {/* Vertical label + Archetype filter */}
        <div className="flex flex-wrap items-center gap-4">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--nn-navy)] bg-[color-mix(in_srgb,var(--nn-navy)_10%,transparent)] px-4 py-1.5 font-heading text-[0.78rem] font-semibold text-[var(--nn-navy)]">
            Vertical: Geopolitics
          </span>
          <div className="h-6 w-px bg-[var(--nn-border)]" />
          <ArchetypePills />
        </div>

        {/* T2a: Lens toggle */}
        <div className="mt-4 flex items-center gap-3">
          <LensToggle lens={lens} onChange={setLens} />
        </div>
        <p className="mt-1 font-sans text-[0.85rem] text-[var(--nn-text-dim)]">
          {lens === "consensus"
            ? "Origination vs Validation — how often each source breaks stories vs how often those stories become consensus. Only graded sources shown."
            : "Claim volume vs Solo Coverage Share — every source plotted. High-solo sources cover stories no one else in the panel does; low-solo sources report the shared news cycle."}
        </p>

        {lens === "consensus" ? (
          <>
            {/* Scatter plot card */}
            <div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6">
              <div className="mb-3 flex items-baseline justify-between gap-2">
                <h2 className="font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
                  The Reputation Map
                </h2>
              </div>
              <p className="mb-3 font-sans text-[0.85rem] text-[var(--nn-text-dim)]">
                Each dot is a news outlet, plotted by origination (how often it
                reports claims before the panel) vs validation (how often those
                claims later enter consensus).
              </p>
              {/* E2: caption — upper-right of chart, Space Grotesk, navy accent, gentle slide-in per animate skill */}
              <p className="mb-3 text-right font-heading text-[0.95rem] font-medium text-[var(--nn-navy)] animate-[caption-in_0.5s_cubic-bezier(0.16,1,0.3,1)]">
                {visibleSources.length} outlets ·{" "}
                {daySpan != null ? `${daySpan} days` : "multi-year"} of coverage
                — click any dot to see that outlet's full record.
              </p>
              <div className="mb-3 space-y-1 font-sans text-[0.82rem] text-(--nn-text)">
                {[
                  {
                    color: "var(--nn-navy)",
                    label: "Early Breaker",
                    desc: "breaks stories, consensus follows",
                  },
                  {
                    color: "var(--nn-red)",
                    label: "Noise Generator",
                    desc: "breaks stories, rarely absorbed",
                  },
                  {
                    color: "var(--nn-teal)",
                    label: "Selective but Accurate",
                    desc: "late, reliable",
                  },
                  {
                    color: "var(--nn-slate)",
                    label: "Consensus Follower",
                    desc: "safe, uninformative",
                  },
                ].map((item) => (
                  <div key={item.label} className="flex items-baseline gap-1.5">
                    <span
                      className="mt-[0.3em] inline-block h-2.5 w-2.5 shrink-0 rounded-[2px]"
                      style={{ backgroundColor: item.color }}
                    />
                    <span>
                      <span style={{ color: item.color }}>{item.label}</span>
                      <span className="text-[var(--nn-text-dim)]">
                        {" "}
                        — {item.desc}
                      </span>
                    </span>
                  </div>
                ))}
                <div className="mt-1.5 font-sans text-[0.82rem] text-[var(--nn-text-dim)]">
                  Shapes: ● Wire/Consensus Anchor · ■ Mainstream Editorial · ◆
                  International · ▲ Investigative · ✚ Contrarian
                </div>
              </div>
              <ScatterPlot
                data={gradedData}
                hoveredId={hoveredSource}
                onHoverPosition={handleHoverPosition}
                onSelect={handleSelect}
              />
              {tooltipPos &&
                hoveredSource &&
                (() => {
                  const source = scatterData.find(
                    (s) => s.sourceId === hoveredSource,
                  );
                  if (!source) return null;
                  // A2: clamp tooltip to viewport
                  const tx = Math.min(
                    tooltipPos.x + 12,
                    window.innerWidth - 200,
                  );
                  const ty = Math.min(
                    Math.max(tooltipPos.y - 10, 0),
                    window.innerHeight - 80,
                  );
                  return (
                    <div
                      className="pointer-events-none fixed z-50 rounded-[8px] border border-[var(--nn-border)] bg-[var(--nn-surface)] px-3 py-2 shadow-lg transition-opacity duration-150"
                      style={{
                        left: tx,
                        top: ty,
                      }}
                    >
                      <div className="font-sans text-[0.82rem] font-semibold text-[var(--nn-text)]">
                        {source.name}
                      </div>
                      <div className="font-mono text-[0.82rem] tabular-nums text-[var(--nn-text)]">
                        Tier {source.tier} · Origination{" "}
                        {Math.round(source.R_orig)} · Validation{" "}
                        {source.R_val != null ? Math.round(source.R_val) : "—"}
                      </div>
                      <div className="mt-0.5 font-mono text-[0.75rem] text-[var(--nn-text-dim)]">
                        Click to view profile
                      </div>
                    </div>
                  );
                })()}
            </div>

            {/* Ungraded sources callout (F2c) */}
            {ungradedSources.length > 0 && (
              <div className="mt-3 rounded-[10px] border border-[var(--nn-border)] bg-[var(--nn-surface)] px-4 py-3 font-sans text-[0.85rem] text-[var(--nn-text-dim)]">
                <p>
                  <span className="font-semibold text-[var(--nn-text)]">
                    {ungradedSources.length} source
                    {ungradedSources.length !== 1 ? "s" : ""} not yet graded ⓘ
                  </span>
                </p>
                <p className="mt-1">
                  These outlets mostly cover stories no other panel source
                  reports, so cross-source consensus can't form — a
                  panel-composition trait, not a quality judgment.
                </p>
              </div>
            )}

            {AboutValidationCard()}
          </>
        ) : (
          <>
            {/* T3: Coverage Landscape scatter */}
            <div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6">
              <h2 className="font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
                Coverage Landscape
              </h2>
              <div className="h-[420px]">
                <ScatterPlot
                  data={coverageScatter}
                  hoveredId={hoveredSource}
                  onHoverPosition={handleHoverPosition}
                  onSelect={handleSelect}
                  xScale="log"
                  xLabel="Claim volume (log)"
                  yLabel="Solo coverage share %"
                  showQuadrants={false}
                  regions={[
                    {
                      yMin: 60,
                      yMax: 100,
                      label: "Sole voices",
                      sublabel: "uncorroborated coverage",
                    },
                    {
                      yMin: 0,
                      yMax: 30,
                      label: "Consensus arena",
                      sublabel: "cross-source overlap",
                    },
                  ]}
                />
              </div>
            </div>
          </>
        )}

        {/* Ledger card */}
        <div
          id="full-ledger"
          className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6"
        >
          <h2 className="font-heading text-[1.15rem] font-bold text-(--nn-text)">
            Full Ledger
          </h2>
          <div className="mb-4 flex flex-wrap items-start justify-between gap-5">
            <Legend />

            <DemoCorpusNote />
          </div>

          <p className="mb-2 text-center font-mono text-[0.75rem] text-(--nn-text-dim)">
            Click a source row to open its profile. Click column headers to
            sort.
          </p>

          <p className="mb-2 font-sans text-[0.75rem] text-[var(--nn-text-dim)]">
            ↑ higher is better · ↓ lower is better
          </p>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[0.88rem]">
              <thead>
                <tr>
                  <th
                    scope="col"
                    aria-sort={
                      sortKey === "name"
                        ? sortDir === 1
                          ? "ascending"
                          : "descending"
                        : "none"
                    }
                    className="px-2.5 py-2 text-left font-mono text-[0.75rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)] cursor-pointer select-none hover:text-[var(--nn-text)]"
                    onClick={() => handleSort("name")}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        handleSort("name");
                      }
                    }}
                    tabIndex={0}
                  >
                    Source{sortArrow("name")}
                  </th>
                  {SCORE_COLUMNS.map((col) => (
                    <th
                      key={col.key}
                      scope="col"
                      aria-sort={
                        sortKey === col.key
                          ? sortDir === 1
                            ? "ascending"
                            : "descending"
                          : "none"
                      }
                      title={
                        col.direction === "higher"
                          ? "Higher is better"
                          : col.direction === "lower"
                            ? "Lower is better"
                            : ""
                      }
                      className="px-2.5 py-2 text-left font-mono text-[0.75rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)] cursor-pointer select-none hover:text-[var(--nn-text)]"
                      onClick={() => handleSort(col.key)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          handleSort(col.key);
                        }
                      }}
                      tabIndex={0}
                    >
                      {col.label}
                      {col.direction === "higher"
                        ? " ↑"
                        : col.direction === "lower"
                          ? " ↓"
                          : ""}
                      {sortArrow(col.key)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map(({ source, score, dimmed }) => (
                  <tr
                    key={source.id}
                    data-source-id={source.id}
                    className={`border-b border-[var(--nn-border)] hover:bg-[var(--nn-surface2)] transition-colors cursor-pointer${
                      dimmed ? " opacity-15" : ""
                    }`}
                    onMouseEnter={() => setHoveredSource(source.id)}
                    onMouseLeave={() => setHoveredSource(null)}
                    onClick={() => navigate(`/source/${source.domain}`)}
                  >
                    <td className="px-2.5 py-2.5 font-semibold text-[0.9rem]">
                      <span className="text-[var(--nn-navy)] cursor-pointer hover:underline">
                        {source.name}
                      </span>
                      <span className="ml-2 font-mono text-[0.78rem] font-normal text-[var(--nn-text-dim)]">
                        {source.domain}
                      </span>
                    </td>
                    {SCORE_COLUMNS.map((col) => (
                      <td
                        key={col.key}
                        className="px-2.5 py-2.5 font-mono text-[0.8rem] tabular-nums text-[var(--nn-text)]"
                      >
                        {score != null
                          ? Math.round(score[col.key] as number)
                          : "—"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
