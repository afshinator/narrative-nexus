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
import VfTrendChart from "../components/VfTrendChart";
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

// ── Dead dimensions in demo corpus — UX10 finding 2 ──
const DEAD_DIMS = new Set(["R_edit", "R_correct"]);

// ── Live radar dimensions (exclude dead ones) ──
const RADAR_DIMS = DIMENSIONS.filter((d) => !DEAD_DIMS.has(d.key));

const SPARKLINE_WINDOW = 30; // trailing days for sparklines
const STAT_DELTA_THRESHOLD = 1; // delta < 1pt = · (flat)

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
			{/* P5: 1 — Page header */}
			<div className="flex items-center gap-3">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					{source.name}
				</h1>
			</div>
			<p className="-mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
				Tier {source.tier} &middot; {source.domain}
			</p>
			<p className="font-sans text-[0.85rem] text-[var(--nn-navy)]">
				<Link to="/cluster/966" className="hover:underline">
					View cluster → US-Iran War: March Escalation &amp; April Ceasefire
				</Link>
			</p>

			{/* Vertical picker pills */}
			<VerticalPills vertical={vertical} onChange={setVertical} />

			{/* P5: 2 — Archetype badge + radar + stat panel row */}
			<div className="grid gap-6 lg:grid-cols-[280px_1fr]">
				<StatPanel
					snapshot={latestSnapshot}
					baseline={baseline}
					medianOrig={panelMedianOrig}
					medianVal={panelMedianVal}
				/>
				<RadarChart
					snapshot={latestSnapshot}
					baseline={baseline}
					tierAvg={tierAvg}
				/>
			</div>

			{/* P5: 3 — Claim Flow */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
				<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-1">
					Claim Flow
				</h2>
				<p className="mb-3 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
					Of the {claimSummary.total} claims this source contributed to, how many entered consensus, are pending, or expired unresolved
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
						<p className="font-mono text-[0.72rem] text-[var(--nn-text-dim)] pt-1">
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
									<th className="px-2 py-2 text-left font-mono text-[0.7rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)]">
										Article
									</th>
									<th className="px-2 py-2 text-right font-mono text-[0.7rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)]">
										Change
									</th>
									<th className="px-2 py-2 text-right font-mono text-[0.7rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)]">
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

			{/* P5: 5 — Sparklines + Vf Trend (last) */}
			<SparklineGrid
				snapshots={filtered}
				latestSnapshot={latestSnapshot}
			/>

			<VfTrendChart snapshots={filtered} />
		</div>
	);
}

// ─── Sub-components ───

function StatPanel({
	snapshot,
	baseline,
	medianOrig,
	medianVal,
}: {
	snapshot: DailySnapshot | null;
	baseline: DailySnapshot | null;
	medianOrig: number;
	medianVal: number;
}) {
	const archetype = snapshot
		? getArchetype(snapshot.R_orig, snapshot.R_val, medianOrig, medianVal)
		: null;

	return (
		<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
			{/* Archetype badge */}
			<span
				className={`inline-block rounded-full px-3 py-1 font-mono text-[0.66rem] font-semibold uppercase tracking-[0.04em] ${
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

			{/* Stat rows */}
			<div className="mt-3 space-y-0">
				{DIMENSIONS.map((dim) => {
					const value = snapshot?.[dim.key] as number | undefined;
					const baselineVal = baseline?.[dim.key] as number | undefined;
					const isDead = DEAD_DIMS.has(dim.key);

					// P3: Dead dimensions show "no events detected"
					if (isDead && (value == null || value === 0)) {
						return (
							<div
								key={dim.key}
								className="flex items-baseline justify-between border-b border-[var(--nn-border)] py-1.5 last:border-b-0"
							>
								<span className="text-[0.76rem] text-[var(--nn-text-dim)]">
									{dim.label}
								</span>
								<span className="text-[0.72rem] italic text-[var(--nn-text-dim)]">
									no events detected
								</span>
							</div>
						);
					}

					const hasDelta = value != null && baselineVal != null;
					const diff = hasDelta ? value! - baselineVal! : undefined;
					const dir: "up" | "down" | "flat" =
						diff != null
							? Math.abs(diff) < STAT_DELTA_THRESHOLD
								? "flat"
								: diff > 0
									? "up"
									: "down"
							: "flat";
					const arrow = dir === "up" ? "▲" : dir === "down" ? "▼" : "·";
					const arrowColor =
						dir === "up"
							? "text-[var(--nn-teal)]"
							: dir === "down"
								? "text-[var(--nn-red)]"
								: "text-[var(--nn-text-dim)]";
					const valueColor =
						value != null ? getPolarityColor(dim.key, value) : "";

					return (
						<div
							key={dim.key}
							className="flex items-baseline justify-between border-b border-[var(--nn-border)] py-1.5 last:border-b-0"
						>
							<span className="text-[0.76rem] text-[var(--nn-text-dim)]">
								{dim.label}
								{dim.trait && <span className="opacity-50"> (trait)</span>}
							</span>
							<span className="flex items-baseline gap-1.5">
								<span
									className="font-mono text-[0.78rem] tabular-nums"
									style={{ color: valueColor || "var(--nn-text)" }}
								>
									{value != null ? Math.round(value) : "—"}
								</span>
								{hasDelta && (
									<span className={`font-mono text-[0.66rem] ${arrowColor}`}>
										{arrow}
										{Math.abs(Math.round(diff!)).toString()}
									</span>
								)}
							</span>
						</div>
					);
				})}
			</div>
		</div>
	);
}

function RadarChart({
	snapshot,
	baseline,
	tierAvg,
}: {
	snapshot: DailySnapshot | null;
	baseline: DailySnapshot | null;
	tierAvg?: number[];
}) {
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
				label: "Current",
				data: curVal ?? [],
				borderColor: "var(--nn-teal)",
				// P2: raised fill alpha from 0.13 to 0.22 for dark-mode visibility
				backgroundColor: "rgba(94,189,142,0.22)",
				borderWidth: 2,
				pointRadius: hasData ? 3 : 0,
				pointBackgroundColor: "var(--nn-teal)",
			},
			...(baseVal
				? [
						{
							label: "Day 0 baseline",
							data: baseVal,
							borderColor: "rgba(115,133,103,0.55)",
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
							label: "Tier avg",
							data: tierAvg
								.filter((_, i) => i < RADAR_DIMS.length)
								.map((v, i) =>
									INVERTED_DIMS.has(RADAR_DIMS[i].key) ? 100 - v : v,
								),
							borderColor: "var(--nn-slate)",
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
					// P2: tick labels to --nn-text for dark-mode visibility
					color: "var(--nn-text)",
					font: { size: 9 },
				},
				pointLabels: {
					// P2: axis labels to --nn-text for dark-mode visibility
					color: "var(--nn-text)",
					font: { size: 10, family: "'IBM Plex Mono', monospace" },
				},
				grid: { color: "var(--nn-border)" },
				angleLines: { color: "var(--nn-border)" },
			},
		},
		plugins: {
			legend: {
				position: "bottom" as const,
				labels: {
					color: "var(--nn-text-dim)",
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
			{hasData ? (
				<>
					<div className="h-[340px]">
						<Radar data={data} options={options} />
					</div>
					{/* P3: caption for dead dimensions */}
					<p className="mt-2 text-center font-sans text-[0.7rem] italic text-[var(--nn-text-dim)]">
						Silent Edits and Corrections omitted — no edit or correction events in demo corpus
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

function SparklineGrid({
	snapshots,
	latestSnapshot,
}: {
	snapshots: DailySnapshot[];
	latestSnapshot: DailySnapshot | null;
}) {
	// P1: Use trailing 30 days from the latest snapshot, not currentDay
	const latestDay = useMemo(() => {
		if (snapshots.length === 0) return 0;
		const sorted = [...snapshots].sort((a, b) => a.day - b.day);
		return sorted[sorted.length - 1].day;
	}, [snapshots]);

	const sparkData = useMemo(() => {
		if (snapshots.length === 0) return null;
		const sorted = [...snapshots].sort((a, b) => a.day - b.day);
		const startDay = Math.max(0, latestDay - SPARKLINE_WINDOW);
		const window = sorted.filter(
			(s) => s.day >= startDay && s.day <= latestDay,
		);

		return DIMENSIONS.map((dim) => {
			const values = window.map((s) => s[dim.key] as number);
			if (values.length === 0) return { dim, points: "" };
			const min = Math.min(...values);
			const max = Math.max(...values);
			const range = max - min || 1;
			const pts = values.map((v, i) => {
				const x = (i / Math.max(values.length - 1, 1)) * 30;
				const y = 20 - ((v - min) / range) * 16 - 2;
				return `${x.toFixed(1)},${y.toFixed(1)}`;
			});
			return { dim, points: pts.join(" ") };
		});
	}, [snapshots, latestDay]);

	const currentVal = latestSnapshot;

	return (
		<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
			<h2 className="mb-1 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
				30-Day Trends
			</h2>
			<p className="mb-3 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
				How each score moved over the last 30 days
			</p>
			<div className="grid grid-cols-2 gap-x-6 gap-y-2">
				{DIMENSIONS.map((dim) => {
					const spark = sparkData?.find((s) => s.dim.key === dim.key);
					const val = currentVal?.[dim.key] as number | undefined;
					const isDead = DEAD_DIMS.has(dim.key) && (val == null || val === 0);
					return (
						<div key={dim.key} className="flex items-center gap-2">
							<span className="w-28 flex-shrink-0 text-right font-mono text-[0.66rem] text-[var(--nn-text-dim)]">
								{dim.label}
							</span>
							{isDead ? (
								<span className="flex-1 text-[0.66rem] italic text-[var(--nn-text-dim)]">
									no events
								</span>
							) : (
								<svg
									viewBox="0 0 30 20"
									className="h-5 flex-1"
									role="img"
									aria-label={`${dim.label} trend`}
								>
									{spark?.points ? (
										<polyline
											fill="none"
											stroke="var(--nn-teal)"
											strokeWidth="1.2"
											points={spark.points}
										/>
									) : null}
								</svg>
							)}
							<span className="w-9 text-right font-mono text-[0.66rem] tabular-nums text-[var(--nn-text)]">
								{val != null ? Math.round(val) : "—"}
							</span>
						</div>
					);
				})}
			</div>
		</div>
	);
}

// DayScrubber kept in codebase but unmounted — removed from page per UX11-P1

export default SourceProfilePage;
