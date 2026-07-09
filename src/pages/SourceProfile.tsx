import {
	Chart as ChartJS,
	Filler,
	Legend,
	LineElement,
	PointElement,
	RadialLinearScale,
	Tooltip,
} from "chart.js";
import {
	useEffect,
	useMemo,
	useState,
} from "react";
import { Radar } from "react-chartjs-2";
import { Link, useParams } from "react-router";
import VerticalPills from "../components/VerticalPills";
import type { DailySnapshot } from "../data/scores";

// ── Inline types for new profile sections ──
// ponytail: defined here, not in a separate file
interface SilentEdit {
	id: number;
	change_ratio: number;
	stored_body_length: number;
	fetched_body_length: number;
	detected_at: string;
	article_url: string;
	article_title: string | null;
}

interface ClaimSummary {
	total: number;
	absorbed: number;
	pending: number;
	unresolved: number;
}

import { DIMENSIONS } from "../data/scores";
import { DEFAULT_SOURCES } from "../data/sources";
import type { VerticalThresholdKey } from "../data/thresholds";
import { getArchetype } from "../utils/archetype";
import { getPolarityColor, INVERTED_DIMS } from "../utils/polarity";

ChartJS.register(
	RadialLinearScale,
	PointElement,
	LineElement,
	Filler,
	Tooltip,
	Legend,
);

// ── Dimensions not exercised in the shipped dataset — UX10 finding 2 ──
const DEAD_DIMS = new Set(["R_edit", "R_correct"]);

// ── Live radar dimensions (exclude dead ones) ──
const RADAR_DIMS = DIMENSIONS.filter((d) => !DEAD_DIMS.has(d.key));

// SPARKLINE_WINDOW removed — SparklineGrid cut per UX14-V2
// ponytail: STAT_DELTA_THRESHOLD removed — Δ annotations cut per UX15-B

interface Props {
	snapshots?: DailySnapshot[];
	tierAvg?: number[];
	panelMedian?: { orig: number; val: number };
}

function SourceProfilePage({
	snapshots: _initialSnapshots = [],
	tierAvg: _initialTierAvg,
	panelMedian: _initialPanelMedian = { orig: 50, val: 50 },
}: Props) {
	const { domain } = useParams<{ domain: string }>();
	const source = useMemo(
		() => DEFAULT_SOURCES.find((s) => s.domain === domain),
		[domain],
	);

	const [vertical, setVertical] = useState<VerticalThresholdKey>("geopolitics");

	// Fetch profile data from API
	const [fetchedSnapshots, setFetchedSnapshots] = useState<DailySnapshot[]>([]);
	const [tierAvg, setTierAvg] = useState<number[] | undefined>(_initialTierAvg);
	const [panelMedian, setPanelMedian] = useState(_initialPanelMedian);
	const [fetchedEdits, setFetchedEdits] = useState<SilentEdit[]>([]);
	const [claimSummary, setClaimSummary] = useState<ClaimSummary>({
		total: 0,
		absorbed: 0,
		pending: 0,
		unresolved: 0,
	});

	useEffect(() => {
		let cancelled = false;
		async function load() {
			try {
				const srcResp = await fetch("/api/sources");
				if (!srcResp.ok) return;
				const srcData = await srcResp.json();
				const dbSource = (
					srcData.sources as { id: number; domain: string }[]
				).find((s) => s.domain === domain);
				if (!dbSource || cancelled) return;
				const resp = await fetch(
					`/api/sources/${dbSource.id}/profile?vertical=${vertical}`,
				);
				if (!resp.ok) return;
				const data = await resp.json();
				if (cancelled) return;
				setFetchedSnapshots(data.snapshots ?? []);
				setTierAvg(data.tierAvg);
				setPanelMedian(data.panelMedian ?? { orig: 50, val: 50 });
				setFetchedEdits((data.edits as SilentEdit[]) ?? []);
				setClaimSummary(
					(data.claimSummary as ClaimSummary) ?? {
						total: 0,
						absorbed: 0,
						pending: 0,
						unresolved: 0,
					},
				);
			} catch {
				// Keep defaults on error
			}
		}
		load();
		return () => {
			cancelled = true;
		};
	}, [domain, vertical]);

	const snapshots =
		fetchedSnapshots.length > 0 ? fetchedSnapshots : _initialSnapshots;

	// Filter snapshots by vertical
	const filtered = useMemo(
		() => snapshots.filter((s) => s.vertical === vertical),
		[snapshots, vertical],
	);

	// P1: Use latest snapshot (last by day), not interpolated time-machine
	const latestSnapshot = useMemo(() => {
		if (filtered.length === 0) return null;
		const sorted = [...filtered].sort((a, b) => a.day - b.day);
		return sorted[sorted.length - 1];
	}, [filtered]);

	// Day-0 baseline for delta computation
	const baseline = useMemo(
		() => filtered.find((s) => s.day === 0) ?? null,
		[filtered],
	);

	// Panel median values from prop
	const panelMedianOrig = panelMedian.orig;
	const panelMedianVal = panelMedian.val;

	// --- Source not found ---
	if (!source) {
		return (
			<div className="mx-auto max-w-[1340px] py-16 text-center">
				<h1 className="font-heading text-[2rem] font-bold text-[var(--nn-text)]">
					Source not found
				</h1>
				<p className="mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
					&ldquo;{domain}&rdquo; is not in the tracked panel.
				</p>
				<Link
					to="/"
					className="mt-4 inline-block font-mono text-[0.84rem] text-[var(--nn-navy)] hover:underline"
				>
					&larr; Back to Sources
				</Link>
			</div>
		);
	}

	return (
		<div className="mx-auto max-w-[1340px] space-y-6">
			{/* UX15 title block */}
			<p className="font-mono text-[0.75rem] uppercase tracking-[0.12em] text-[var(--nn-text-dim)]">
				Source Profile
			</p>
			<div className="flex items-center gap-3">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					{source.name}
				</h1>
			</div>
			<p className="-mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
				Tier {source.tier} &middot; {source.tier === 1 ? "Wire/Consensus Anchor"
					: source.tier === 2 ? "Mainstream Editorial"
					: source.tier === 3 ? "International"
					: source.tier === 4 ? "Independent/Investigative"
					: "Contrarian"} &middot; {source.domain}
			</p>
			<p className="font-sans text-[0.85rem] text-[var(--nn-text-dim)]">
				How this outlet behaves across the monitored panel — scores, archetype, and claim outcomes.
			</p>
			<p className="font-sans text-[0.85rem] text-[var(--nn-navy)]">
				<Link to="/cluster/966" className="hover:underline">
					View cluster → US-Iran War: March Escalation &amp; April Ceasefire
				</Link>
			</p>

			{/* Vertical picker pills */}
			<VerticalPills vertical={vertical} onChange={setVertical} />

			{/* M1: Percentile explainer */}
			<p className="font-sans text-[0.85rem] leading-relaxed text-[var(--nn-text-dim)]">
				All scores are percentile ranks within the monitored panel —
				100 means this source leads the panel on that measure, 50 is median.
			</p>

			{/* P5: 2 — Archetype badge + radar + stat panel row */}
			<div className="grid gap-6 lg:grid-cols-[280px_1fr]">
				<StatPanel
					snapshot={latestSnapshot}
					medianOrig={panelMedianOrig}
					medianVal={panelMedianVal}
				/>
				<RadarChart
					snapshot={latestSnapshot}
					baseline={baseline}
					tierAvg={tierAvg}
					tier={source.tier}
				/>
			</div>

			{/* P5: 3 — Claim Flow */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
				<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-1">
					Claim Flow
				</h2>
				<p className="mb-3 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
					Of the {claimSummary.total} claims this source contributed to, how many entered consensus, are pending, or expired unresolved. Pending claims are awaiting corroboration from other panel sources — most single-source regional claims stay pending.
				</p>
				{claimSummary.total > 0 ? (
					<div className="space-y-2">
						<div className="flex items-center gap-3">
							<span className="w-24 font-mono text-[0.78rem] text-[var(--nn-text-dim)]">
								Absorbed
							</span>
							{claimSummary.absorbed === 0 ? (
								<span className="flex-1 text-[0.8rem] text-[var(--nn-text-dim)]">
									0 of {claimSummary.total} claims have crossed corroboration threshold
								</span>
							) : (
								<>
									<div className="flex-1 h-5 rounded-sm bg-[var(--nn-surface2)] overflow-hidden">
										<div
											className="h-full rounded-sm bg-[var(--nn-teal)]"
											style={{
												width: `${(claimSummary.absorbed / claimSummary.total) * 100}%`,
											}}
										/>
									</div>
									<span className="w-20 text-right font-mono text-[0.78rem] tabular-nums text-[var(--nn-text)]">
										{claimSummary.absorbed} (
										{Math.round((claimSummary.absorbed / claimSummary.total) * 100)}
										%)
									</span>
								</>
							)}
						</div>
						<div className="flex items-center gap-3">
							<span className="w-24 font-mono text-[0.78rem] text-[var(--nn-text-dim)]">
								Pending
							</span>
							<div className="flex-1 h-5 rounded-sm bg-[var(--nn-surface2)] overflow-hidden">
								<div
									className="h-full rounded-sm bg-[var(--nn-navy)]"
									style={{
										width: `${(claimSummary.pending / claimSummary.total) * 100}%`,
									}}
								/>
							</div>
							<span className="w-20 text-right font-mono text-[0.78rem] tabular-nums text-[var(--nn-text)]">
								{claimSummary.pending} (
								{Math.round((claimSummary.pending / claimSummary.total) * 100)}
								%)
							</span>
						</div>
						{claimSummary.unresolved > 0 && (
							<div className="flex items-center gap-3">
								<span className="w-24 font-mono text-[0.78rem] text-[var(--nn-text-dim)]">
									Unresolved
								</span>
								<div className="flex-1 h-5 rounded-sm bg-[var(--nn-surface2)] overflow-hidden">
									<div
										className="h-full rounded-sm"
										style={{
											width: `${(claimSummary.unresolved / claimSummary.total) * 100}%`,
											backgroundColor: "var(--nn-slate)",
										}}
									/>
								</div>
								<span className="w-20 text-right font-mono text-[0.78rem] tabular-nums text-[var(--nn-text)]">
									{claimSummary.unresolved} (
									{Math.round((claimSummary.unresolved / claimSummary.total) * 100)}
									%)
								</span>
							</div>
						)}
						<p className="font-mono text-[0.75rem] text-[var(--nn-text-dim)] pt-1">
							{claimSummary.total} claims contributed to by this source
						</p>
					</div>
				) : (
					<p className="text-[var(--nn-text-dim)] text-[0.85rem]">
						No claims attributed.
					</p>
				)}
			</div>

			{/* P5: 4 — Silent Edit Log */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
				<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-3">
					Silent Edit Log
				</h2>
				{fetchedEdits.length > 0 ? (
					<div className="overflow-x-auto">
						<table className="w-full border-collapse text-[0.82rem]">
							<thead>
								<tr>
									<th className="px-2 py-2 text-left font-mono text-[0.75rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)]">
										Article
									</th>
									<th className="px-2 py-2 text-right font-mono text-[0.75rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)]">
										Change
									</th>
									<th className="px-2 py-2 text-right font-mono text-[0.75rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)]">
										Stored → Fetched
									</th>
								</tr>
							</thead>
							<tbody>
								{fetchedEdits.map((edit) => {
									const pct = Math.round(edit.change_ratio * 100);
									const severityClass =
										pct > 30
											? "text-[var(--nn-red)]"
											: pct > 10
												? "text-[var(--nn-amber)]"
												: "text-[var(--nn-teal)]";
									return (
										<tr
											key={edit.id}
											className="border-b border-[var(--nn-border)] last:border-b-0"
										>
											<td className="px-2 py-2 max-w-[400px] truncate">
												<a
													href={edit.article_url}
													target="_blank"
													rel="noopener noreferrer"
													className="text-[var(--nn-text)] hover:text-[var(--nn-teal)] transition-colors"
												>
													{edit.article_title ?? edit.article_url}
												</a>
											</td>
											<td
												className={`px-2 py-2 text-right font-mono tabular-nums ${severityClass}`}
											>
												{pct}%
											</td>
											<td className="px-2 py-2 text-right font-mono text-[0.75rem] tabular-nums text-[var(--nn-text-dim)]">
												{edit.stored_body_length.toLocaleString()} →{" "}
												{edit.fetched_body_length.toLocaleString()}
											</td>
										</tr>
									);
								})}
							</tbody>
						</table>
					</div>
				) : (
					<p className="text-[var(--nn-text-dim)] text-[0.85rem]">
						No silent edits detected.
					</p>
				)}
			</div>

			{/* SparklineGrid + VfTrendChart unmounted per UX14 — percentile-rank noise */}

		</div>
	);
}

// ─── Sub-components ───

function StatPanel({
	snapshot,
	medianOrig,
	medianVal,
}: {
	snapshot: DailySnapshot | null;
	medianOrig: number;
	medianVal: number;
}) {
	const archetype = snapshot
		? getArchetype(snapshot.R_orig, snapshot.R_val, medianOrig, medianVal)
		: null;

	// UX15-B: Two-tier layout — hero row (Origination/Validation) + secondary (Speed/Framing)
	// ponytail: dead dims collapsed to one line, meaning clauses and Δ removed
	const HERO_DIMS = [
		{ key: "R_orig", label: "Origination" },
		{ key: "R_val", label: "Validation" },
	];
	const SUB_DIMS = [
		{ key: "R_speed", label: "Speed" },
		{ key: "R_frame", label: "Framing" },
	];
	const noDeadEvents = snapshot != null
		&& (snapshot.R_edit == null || snapshot.R_edit === 0)
		&& (snapshot.R_correct == null || snapshot.R_correct === 0);

	return (
		<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
			{/* Archetype badge */}
			<span
				className={`inline-block rounded-full px-3 py-1 font-mono text-[0.75rem] font-semibold uppercase tracking-[0.04em] ${
					archetype
						? {
								EARLY_BREAKER: "bg-[var(--nn-navy)]/10 text-[var(--nn-navy)]",
								NOISE_GENERATOR: "bg-[var(--nn-red)]/10 text-[var(--nn-red)]",
								SELECTIVE_ACCURATE:
									"bg-[var(--nn-teal)]/10 text-[var(--nn-teal)]",
								CONSENSUS_FOLLOWER:
									"bg-[var(--nn-slate)]/10 text-[var(--nn-slate)]",
							}[archetype]
						: "text-[var(--nn-text-dim)]"
				}`}
			>
				{archetype ? archetype.replace(/_/g, " ") : "Unclassified"}
			</span>

			{/* UX15-B: Hero row — Origination + Validation (scatter-plot axes) */}
			<div className="mt-3 flex justify-around">
				{HERO_DIMS.map((dim) => {
					const value = snapshot?.[dim.key as keyof DailySnapshot] as number | undefined;
					const valueColor = value != null ? getPolarityColor(dim.key, value) : "";
					return (
						<div key={dim.key} className="text-center">
							<span
								className="block font-heading text-[1.65rem] font-bold leading-none tabular-nums"
								style={{ color: valueColor || "var(--nn-text)" }}
							>
								{value != null ? Math.round(value) : "—"}
							</span>
							<span className="mt-0.5 block font-mono text-[0.75rem] uppercase tracking-[0.05em] text-[var(--nn-text-dim)]">
								{dim.label}
							</span>
						</div>
					);
				})}
			</div>

			{/* Secondary row — Speed + Framing */}
			<div className="mt-2 flex justify-around">
				{SUB_DIMS.map((dim) => {
					const value = snapshot?.[dim.key as keyof DailySnapshot] as number | undefined;
					const valueColor = value != null ? getPolarityColor(dim.key, value) : "";
					return (
						<div key={dim.key} className="text-center">
							<span
								className="block font-mono text-[0.82rem] font-semibold tabular-nums"
								style={{ color: valueColor || "var(--nn-text)" }}
							>
								{value != null ? Math.round(value) : "—"}
							</span>
							<span className="mt-0.5 block font-mono text-[0.75rem] uppercase tracking-[0.05em] text-[var(--nn-text-dim)]">
								{dim.label}
							</span>
						</div>
					);
				})}
			</div>

			{/* Dead dims collapsed */}
			{noDeadEvents && (
				<p className="mt-2 text-center font-mono text-[0.75rem] text-[var(--nn-text-dim)]">
					No silent edits or corrections detected
				</p>
			)}
		</div>
	);
}

function RadarChart({
	snapshot,
	baseline,
	tierAvg,
	tier,
}: {
	snapshot: DailySnapshot | null;
	baseline: DailySnapshot | null;
	tierAvg?: number[];
	tier: number;
}) {
	/**
	 * Resolve a CSS custom property to its actual hex value for Chart.js canvas rendering.
	 * Canvas2D fillStyle/strokeStyle does NOT resolve CSS var() — must read from the DOM.
	 */
	function cssVar(name: string): string {
		if (typeof document === "undefined") return "#888";
		return (
			getComputedStyle(document.documentElement).getPropertyValue(name).trim() ||
			"#888"
		);
	}

	/** Convert hex color to rgba with the given alpha. */
	function hexToRgba(hex: string, alpha: number): string {
		const h = hex.replace("#", "");
		const r = parseInt(h.slice(0, 2), 16);
		const g = parseInt(h.slice(2, 4), 16);
		const b = parseInt(h.slice(4, 6), 16);
		return `rgba(${r},${g},${b},${alpha})`;
	}

	// Resolve theme colors once for use across datasets + options
	const teal = cssVar("--nn-teal");
	const slate = cssVar("--nn-slate");
	const text = cssVar("--nn-text");
	const textDim = cssVar("--nn-text-dim");
	const border = cssVar("--nn-border");

	// P3: Use RADAR_DIMS (excludes dead R_edit/R_correct)
	const toRadarValues = (s: DailySnapshot | null): number[] | undefined => {
		if (!s) return undefined;
		const vals = RADAR_DIMS.map((d) => {
			const v = s[d.key] as number | null;
			if (v == null) return null;
			return INVERTED_DIMS.has(d.key) ? 100 - v : v;
		});
		if (vals.some((v) => v == null)) return undefined;
		return vals as number[];
	};

	const curVal = toRadarValues(snapshot);
	const baseVal = toRadarValues(baseline);

	const hasData = curVal != null;

	const data = {
		labels: RADAR_DIMS.map((d) => d.label),
		datasets: [
			{
				label: "This source",
				data: curVal ?? [],
				borderColor: teal,
				backgroundColor: hexToRgba(teal, 0.22),
				borderWidth: 2,
				pointRadius: hasData ? 3 : 0,
				pointBackgroundColor: teal,
			},
			...(baseVal
				? [
						{
							label: "Day 0 baseline",
							data: baseVal,
							borderColor: hexToRgba(textDim, 0.55),
							backgroundColor: "transparent",
							borderWidth: 1.3,
							borderDash: [4, 3],
							pointRadius: 0,
						},
					]
				: []),
			...(tierAvg
				? [
						{
							label: `Tier ${tier} average (its peer group)`,
							data: tierAvg
								.filter((_, i) => i < RADAR_DIMS.length)
								.map((v, i) =>
									INVERTED_DIMS.has(RADAR_DIMS[i].key) ? 100 - v : v,
								),
							borderColor: slate,
							backgroundColor: "transparent",
							borderWidth: 1.2,
							borderDash: [2, 3],
							pointRadius: 0,
						},
					]
				: []),
		],
	};

	const options = {
		responsive: true,
		maintainAspectRatio: false,
		scales: {
			r: {
				min: 0,
				max: 100,
				ticks: {
					display: true,
					stepSize: 25,
					backdropColor: "transparent",
					color: text,
					font: { size: 9 },
				},
				pointLabels: {
					color: text,
					font: { size: 10, family: "'IBM Plex Mono', monospace" },
				},
				grid: { color: border },
				angleLines: { color: border },
			},
		},
		plugins: {
			legend: {
				position: "bottom" as const,
				labels: {
					color: textDim,
					font: { size: 10 },
					usePointStyle: true,
					padding: 16,
				},
			},
			tooltip: {
				callbacks: {
					// ponytail: Chart.js types are strict here — cast to any for the custom label formatter
					label: ((ctx: { raw: unknown; dataIndex: number }) => {
						const dim = RADAR_DIMS[ctx.dataIndex];
						const rawVal = snapshot?.[dim.key] as number;
						const radarVal = Number(ctx.raw) || 0;
						if (rawVal != null && INVERTED_DIMS.has(dim.key)) {
							return `${dim.label}: ${rawVal} (radar: ${radarVal.toFixed(0)})`;
						}
						return `${dim.label}: ${radarVal.toFixed(0)}`;
					}) as any,
				},
			},
		},
	};

	return (
		<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
			<h2 className="mb-1 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
				Reputation Radar
			</h2>
			<p className="mb-3 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
				Shape shows where this source leads (outer edge) or trails (center) the panel
			</p>
			{hasData ? (
				<>
					<div className="h-[340px]">
						<Radar data={data} options={options} />
					</div>
					{/* P3: caption for dead dimensions */}
					<p className="mt-2 text-center font-sans text-[0.78rem] italic text-[var(--nn-text-dim)]">
						Silent Edits and Corrections omitted — no edit or correction events in this dataset
					</p>
				</>
			) : (
				<div className="flex h-[340px] items-center justify-center">
					<p className="max-w-[320px] text-center text-[0.85rem] leading-relaxed text-[var(--nn-text-dim)]">
						This source hasn&apos;t crossed the ≥2-source corroboration
						threshold on any claim yet, so its reputation dimensions
						aren&apos;t graded. The radar appears once absorbed claims exist.
					</p>
				</div>
			)}
		</div>
	);
}

// SparklineGrid cut per UX14-V2 (percentile-rank noise, not source behavior)
// DayScrubber kept in codebase but unmounted — removed from page per UX11-P1

export default SourceProfilePage;
