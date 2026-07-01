import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import ArchetypePills from "../components/ArchetypePills";
import ScatterPlot from "../components/ScatterPlot";
import VerticalPills from "../components/VerticalPills";
import type { ReputationScore } from "../data/scores";
import { DEFAULT_SOURCES } from "../data/sources";
import type { VerticalThresholdKey } from "../data/thresholds";
import { VERTICAL_LABELS } from "../data/thresholds";
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
	const [vertical, setVertical] = useState<VerticalThresholdKey>("geopolitics");
	const [fetchedScores, setFetchedScores] = useState<ReputationScore[]>([]);

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
		fetch(`/api/scores?vertical=${vertical}`)
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
	}, [vertical]);

	// ponytail: use fetched scores when available, otherwise props
	const scores = fetchedScores.length > 0 ? fetchedScores : (propScores ?? []);

	const scoreMap = useMemo(
		() =>
			new Map(
				scores
					.filter((s) => s.vertical === vertical)
					.map((s) => [s.sourceId, s]),
			),
		[scores, vertical],
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
					R_val: score?.R_val ?? 0,
					archetype,
				};
			}),
		[scoreMap, panelMedian, visibleSources],
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
		<div className="mx-auto max-w-[1340px] space-y-6">
			{/* Page header */}
			<div className="flex items-center gap-3 mb-1.5">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					Sources
				</h1>
			</div>
			<p className="-mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
				Behavioral reputation across 20 monitored outlets —{" "}
				{VERTICAL_LABELS[vertical]} vertical
			</p>

			{/* Vertical picker + Archetype filter */}
			<div className="flex flex-wrap items-center gap-4">
				<VerticalPills vertical={vertical} onChange={setVertical} />
				<div className="h-6 w-px bg-[var(--nn-border)]" />
				<ArchetypePills />
			</div>

			{/* Scatter plot card */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6">
				<div className="mb-3 flex items-baseline justify-between gap-2">
					<h2 className="font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
						The Reputation Map
					</h2>
				</div>
				<div className="mb-3 space-y-2 font-sans text-[0.78rem] text-[var(--nn-text)]">
					<p>
						<strong>X-axis:</strong> Origination (0–100) — how often this source
						is first to report a story that becomes consensus-absorbed.
					</p>
					<p>
						<strong>Y-axis:</strong> Validation (0–100) — how often this
						source's outlier claims become consensus-absorbed.
					</p>
				</div>
				<div className="mb-3 space-y-1 font-sans text-[0.75rem] text-[var(--nn-text)]">
					{[
						{
							color: "var(--nn-navy)",
							label: "Early Breaker",
							desc: "high origination + high validation — consistently breaks stories that become consensus-absorbed",
						},
						{
							color: "var(--nn-red)",
							label: "Noise Generator",
							desc: "high origination, low validation — frequently first, rarely becomes consensus-absorbed",
						},
						{
							color: "var(--nn-teal)",
							label: "Selective but Accurate",
							desc: "low origination, high validation — late to stories but reliable",
						},
						{
							color: "var(--nn-slate)",
							label: "Consensus Follower",
							desc: "low origination, low validation — safe but uninformative",
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
				</div>
				<ScatterPlot
					data={scatterData}
					hoveredId={hoveredSource}
					onHover={setHoveredSource}
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
								<div className="font-mono text-[0.72rem] tabular-nums text-[var(--nn-text-dim)]">
									Origination {Math.round(source.R_orig)} · Validation{" "}
									{Math.round(source.R_val)}
								</div>
							</div>
						);
					})()}
			</div>

			{/* Ledger card */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6">
				<div className="mb-3 flex items-baseline justify-between gap-2">
					<h2 className="font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
						Full Ledger
					</h2>
				</div>
				<div className="mb-3 space-y-1.5 font-sans text-[0.72rem] text-[var(--nn-text)]">
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
							Framing<span className="text-[var(--nn-text-dim)]">*</span>
						</span>
						<span className="text-[var(--nn-text-dim)]">
							editorial consistency — pending
						</span>
						<span className="font-semibold">Silent Edits</span>
						<span className="text-[var(--nn-text-dim)]">
							rate of unreported article changes
						</span>
						<span className="font-semibold">
							Corrections<span className="text-[var(--nn-text-dim)]">*</span>
						</span>
						<span className="text-[var(--nn-text-dim)]">
							formal correction rate — pending
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
											className="px-2.5 py-2.5 font-mono text-[0.8rem] tabular-nums text-[var(--nn-text-dim)]"
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
	);
}
