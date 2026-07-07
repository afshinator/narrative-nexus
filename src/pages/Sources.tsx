import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import ArchetypePills from "../components/ArchetypePills";
import LensToggle from "../components/LensToggle";
import ScatterPlot from "../components/ScatterPlot";
import Tooltip from "../components/Tooltip";
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

export default function SourcesPage({ scores: propScores }: Props) {
	const navigate = useNavigate();
	const [hoveredSource, setHoveredSource] = useState<string | null>(null);
	const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(
		null,
	);
	const [sortKey, setSortKey] = useState<SortKey>("name");
	const [sortDir, setSortDir] = useState<1 | -1>(1);
	const [fetchedScores, setFetchedScores] = useState<ReputationScore[]>([]);

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
		fetch(`/api/scores?vertical=geopolitics`)
			.then((r) => {
				if (!r.ok) throw new Error("Failed to load scores");
				return r.json();
			})
			.then((data) => {
				if (cancelled) return;
				const raw: ReputationScore[] = data.scores ?? [];
				// Map domain sourceId → slug for DEFAULT_SOURCES lookup
				const mapped = raw.map((s) => ({
					...s,
					sourceId: _domainToSlug.get(s.sourceId) ?? s.sourceId,
				}));
				setFetchedScores(mapped);
			})
			.catch(() => {}); // ponytail: keep default empty state
		return () => {
			cancelled = true;
		};
	}, []);

	// ponytail: useMemo prevents new [] reference on every render before fetch completes.
	// An unstable scores ref cascades into scoreMap → scatterData → D3 rebuild.
	const scores = useMemo(
		() => fetchedScores.length > 0 ? fetchedScores : (propScores ?? []),
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
					() => (filter === null ? scatterData : scatterData.filter((s) => s.archetype === filter)),
					[scatterData, filter],
				);
				const gradedData = useMemo(
					() => scatterVisible.filter((s): s is typeof s & { R_val: number } => s.R_val != null),
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
			{/* U1: Full-width intro strip — sits under the app header, outside page layout */}
			<div className="-mx-8 -mt-7 mb-6 border-b border-[var(--nn-border)] bg-[var(--nn-surface)] px-8 py-5">
				<div className="mx-auto flex max-w-[900px] items-center gap-6">
					<strong className="shrink-0 font-heading text-[1.35rem] leading-tight text-[var(--nn-navy)]">
							Rating not the truth —<br />but identifying consensus reality
						</strong>
					<span className="block w-px self-stretch bg-[var(--nn-border)]" />
					<p className="font-sans text-[1.05rem] leading-relaxed text-[var(--nn-text-dim)]">
						Narrative Nexus tracks how news outlets originate, validate, and correct
						claims across geopolitics, economics, and technology — scoring each source
						0–100 on six independent reputation dimensions.
					</p>
				</div>
			</div>

			<div className="mx-auto max-w-[1340px] space-y-6">
			{/* Page header */}
			<div className="flex items-center gap-3 mb-1.5">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					Sources
				</h1>
			</div>
			<p className="-mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
			Behavioral reputation across{" "}
			<Tooltip content="Curated panel of wire services, mainstream editorial, international, investigative, and contrarian sources across 5 tiers. — design-v1.2 §5">
				{visibleSources.length} monitored outlets
			</Tooltip>{" "}
			— Geopolitics vertical
			</p>

		{/* T4a: Landing copy with live DB counts — U3: derived from scores */}
		<p className="-mt-1 font-sans text-[0.85rem] leading-relaxed text-[var(--nn-text-dim)]">
			{coverageData.filter((s) => s.has_absorbed_claims).length} of{" "}
			{coverageData.length} panel sources have crossed cross-source
			corroboration on at least one claim. The remaining sources produce
			coverage that either overlaps only partially with the panel
			(Consensus lens) or covers stories no other panel source touches
			(Coverage lens).
		</p>

			{/* Vertical label + Archetype filter */}
			<div className="flex flex-wrap items-center gap-4">
				<span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--nn-navy)] bg-[color-mix(in_srgb,var(--nn-navy)_10%,transparent)] px-4 py-1.5 font-heading text-[0.78rem] font-semibold text-[var(--nn-navy)]">
					Vertical: Geopolitics (demo corpus)
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
				? "R_orig vs R_val — how often each source breaks stories vs how often those stories become consensus. Only graded sources shown."
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
				<div className="mb-3 space-y-2 font-sans text-[0.78rem] text-[var(--nn-text)]">
					<p>
						<strong>X-axis:</strong>{" "}
						<Tooltip content="Outlier claim origination: how often a source breaks claims before the rest of the panel reports them. — design-v1.2 §4 (R_orig)">
							Origination (0–100)
						</Tooltip>{" "}
						— how often this source reports claims before the rest of the panel.
					</p>
					<p>
						<strong>Y-axis:</strong>{" "}
						<Tooltip content="Consensus-absorbed: a claim that has entered the consensus version of events. Terminal state. — design-v1.2 §1">
							Validation (0–100)
						</Tooltip>{" "}
						— how often its early claims later enter consensus.
					</p>
				</div>
				<div className="mb-3 space-y-1 font-sans text-[0.82rem] text-[var(--nn-text)]">
					{[
						{
							color: "var(--nn-navy)",
							label: "Early Breaker",
							desc: "high origination + high validation — consistently breaks stories that become consensus-absorbed",
							tip: "High origination + high validation. Consistently breaks outlier claims that later become consensus-absorbed by the panel. — design-v1.2 §4",
						},
						{
							color: "var(--nn-red)",
							label: "Noise Generator",
							desc: "high origination, low validation — frequently first, rarely becomes consensus-absorbed",
							tip: "High origination, low validation. Frequently breaks claims that never enter consensus — systematic noise. — design-v1.2 §1",
						},
						{
							color: "var(--nn-teal)",
							label: "Selective but Accurate",
							desc: "low origination, high validation — late to stories but reliable",
							tip: "Low origination, high validation. Late to stories but their claims reliably enter consensus. — design-v1.2 §4",
						},
						{
							color: "var(--nn-slate)",
							label: "Consensus Follower",
							desc: "low origination, low validation — safe but uninformative",
							tip: "Low origination, low validation. Stays close to the mainstream view without independent breakout claims. — design-v1.2 §1",
						},
					].map((item) => (
						<div key={item.label} className="flex items-baseline gap-1.5">
							<span
								className="mt-[0.3em] inline-block h-2.5 w-2.5 shrink-0 rounded-[2px]"
								style={{ backgroundColor: item.color }}
							/>
							<span>
								<Tooltip content={item.tip}>
									<span style={{ color: item.color }}>{item.label}</span>
								</Tooltip>
								<span className="text-[var(--nn-text-dim)]">
									{" "}
									— {item.desc}
								</span>
							</span>
						</div>
					))}
					<div className="mt-1.5 font-sans text-[0.82rem] text-[var(--nn-text-dim)]">
						Shapes: ● Wire/Consensus Anchor · ■ Mainstream Editorial · ◆ International · ▲ Investigative · ✚ Contrarian
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
						return (
							<div
								className="pointer-events-none fixed z-50 rounded-[8px] border border-[var(--nn-border)] bg-[var(--nn-surface)] px-3 py-2 shadow-lg transition-opacity duration-150"
								style={{
									left: tooltipPos.x + 12,
									top: tooltipPos.y - 10,
								}}
							>
								<div className="font-sans text-[0.82rem] font-semibold text-[var(--nn-text)]">
									{source.name}
								</div>
								<div className="font-mono text-[0.82rem] tabular-nums text-[var(--nn-text)]">
								Tier {source.tier} · Origination {Math.round(source.R_orig)} · Validation{" "}
								{source.R_val != null ? Math.round(source.R_val) : "—"}
								</div>
							</div>
						);
					})()}
			</div>

			{/* Ungraded sources callout (F2c) */}
		{ungradedSources.length > 0 && (
			<div className="mt-3 rounded-[10px] border border-[var(--nn-border)] bg-[var(--nn-surface)] px-4 py-3 font-sans text-[0.85rem] text-[var(--nn-text-dim)]">
				<Tooltip content={`These outlets mostly cover stories no other panel source reports, so cross-source consensus can't form — a panel-composition trait, not a quality judgment. ${ungradedSources.map(s => s.name).join(", ")}`}>
					<span className="font-semibold text-[var(--nn-text)]">
						{ungradedSources.length} source{ungradedSources.length !== 1 ? "s" : ""} not yet graded ⓘ
					</span>
				</Tooltip>
			</div>
		)}

		{/* Shape legend + R_val=0 explanation */}
			<div className="mt-4 flex flex-wrap items-start gap-6 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
				<div>
					<span className="font-semibold text-[var(--nn-text)]">Shapes = Source Tier</span>
					<div>● Wire/Consensus Anchor — Tier 1: Major Wire Services</div>
					<div>■ Mainstream Editorial — Tier 2: National Outlets</div>
					<div>◆ International — Tier 3: Regional / Specialized</div>
					<div>▲ Investigative — Tier 4: Investigative / Alternative</div>
					<div>✚ Contrarian — Tier 5: Propaganda / Fringe</div>
				</div>
				<div className="min-w-0 flex-1 border-l border-[var(--nn-border)] pl-4">
				<span className="font-semibold text-[var(--nn-text)]">About Validation scoring</span>
				<p>
				Validation measures how often a source's claims clear cross-source
				corroboration: at least 2 independent Tier 1–2 sources must report
				the same claim above the vertical's consensus threshold. Sources
				without any absorbed claims in this vertical are ungraded and listed
				separately — this includes mainstream outlets whose claims haven't
				yet cleared cross-source corroboration.
				</p>
				</div>
			</div>
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
														{ yMin: 60, yMax: 100, label: "Sole voices", sublabel: "uncorroborated coverage" },
														{ yMin: 0, yMax: 30, label: "Consensus arena", sublabel: "cross-source overlap" },
													]}
												/>
					</div>
				</div>
			</>
		)}

		{/* Ledger card */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6">
				<div className="mb-3 flex items-baseline justify-between gap-2">
					<h2 className="font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
						Full Ledger
					</h2>
				</div>
				<div className="mb-3 space-y-1.5 font-sans text-[0.85rem] text-[var(--nn-text)]">
					<p>
						Each source scored 0–100 across six reputation dimensions. Click
						column headers to sort.
					</p>
					<div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
						<span className="font-semibold">Origination</span>
						<span className="text-[var(--nn-text-dim)]">
							first to report a story that becomes consensus-absorbed
						</span>
						<span className="font-semibold">Validation</span>
						<span className="text-[var(--nn-text-dim)]">
							claims absorbed by the panel consensus
						</span>
						<span className="font-semibold">Speed</span>
						<span className="text-[var(--nn-text-dim)]">
							how quickly claims spread (lower is faster)
						</span>
						<span className="font-semibold">
							Framing
						</span>
						<span className="text-[var(--nn-text-dim)]">
							consistency of editorial framing across stories
						</span>
						<span className="font-semibold">Silent Edits</span>
						<span className="text-[var(--nn-text-dim)]">
							rate of unreported article changes
						</span>
						<span className="font-semibold">
							Corrections
						</span>
						<span className="text-[var(--nn-text-dim)]">
							rate of formal published corrections
						</span>
					</div>
					<p className="text-[var(--nn-text-dim)]">
						* Not yet computed — shows "—" for all sources. Sources with 0
						Validation have no consensus-absorbed claims yet.
					</p>
				</div>
				<p className="mb-2 font-sans text-[0.72rem] text-[var(--nn-text-dim)]">
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
									className="px-2.5 py-2 text-left font-mono text-[0.7rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)] cursor-pointer select-none hover:text-[var(--nn-text)]"
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
										className="px-2.5 py-2 text-left font-mono text-[0.7rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)] cursor-pointer select-none hover:text-[var(--nn-text)]"
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
									<td className="px-2.5 py-2.5 font-semibold text-[0.9rem] text-[var(--nn-text)]">
										{source.name}
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
