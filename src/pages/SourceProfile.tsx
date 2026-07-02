import {
	Chart as ChartJS,
	Filler,
	Legend,
	LineElement,
	PointElement,
	RadialLinearScale,
	Tooltip,
} from "chart.js";
import { Pause, Play } from "lucide-react";
import {
	startTransition,
	useCallback,
	useEffect,
	useMemo,
	useRef,
	useState,
} from "react";
import { Radar } from "react-chartjs-2";
import { Link, useParams } from "react-router";
import VerticalPills from "../components/VerticalPills";
import VfTrendChart from "../components/VfTrendChart";
import type { DailySnapshot, ProfileEvent } from "../data/scores";

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

const DAY_MAX = 90;
const ANIMATION_SPEED = 0.6; // days per frame
const ANIMATION_INTERVAL = 40; // ms
const SPARKLINE_WINDOW = 30; // trailing days for sparklines
const STAT_DELTA_THRESHOLD = 1; // delta < 1pt = · (flat)

// INVERTED_DIMS now centralized in src/utils/polarity.ts (review-03 H01)

interface Props {
	snapshots?: DailySnapshot[];
	tierAvg?: number[];
	panelMedian?: { orig: number; val: number };
}

/** Interpolate between two snapshots for smooth scrubbing. */
function interpolate(
	a: DailySnapshot,
	b: DailySnapshot,
	day: number,
): DailySnapshot {
	if (day <= a.day) return a;
	if (day >= b.day) return b;
	const t = (day - a.day) / (b.day - a.day || 1);
	return {
		...a,
		day,
		R_orig: a.R_orig + (b.R_orig - a.R_orig) * t,
		R_val: a.R_val + (b.R_val - a.R_val) * t,
		R_speed: a.R_speed + (b.R_speed - a.R_speed) * t,
		R_frame: a.R_frame + (b.R_frame - a.R_frame) * t,
		R_edit: a.R_edit + (b.R_edit - a.R_edit) * t,
		R_correct: a.R_correct + (b.R_correct - a.R_correct) * t,
	};
}

/** Find the two nearest snapshots bracketing a day value. */
function nearestSnapshots(snapshots: DailySnapshot[], day: number) {
	const sorted = [...snapshots].sort((a, b) => a.day - b.day);
	if (sorted.length === 0) return null;
	if (day <= sorted[0].day) return { a: sorted[0], b: sorted[0] };
	for (let i = 0; i < sorted.length - 1; i++) {
		if (day >= sorted[i].day && day <= sorted[i + 1].day) {
			return { a: sorted[i], b: sorted[i + 1] };
		}
	}
	const last = sorted[sorted.length - 1];
	return { a: last, b: last };
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
	const [currentDay, setCurrentDay] = useState(0);
	const [playing, setPlaying] = useState(false);
	const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

	// Fetch profile data from API
	const [fetchedSnapshots, setFetchedSnapshots] = useState<DailySnapshot[]>([]);
	const [tierAvg, setTierAvg] = useState<number[] | undefined>(_initialTierAvg);
	const [panelMedian, setPanelMedian] = useState(_initialPanelMedian);
	const [fetchedEvents, setFetchedEvents] = useState<ProfileEvent[]>([]);
	const [fetchedEdits, setFetchedEdits] = useState<SilentEdit[]>([]);
	const [claimSummary, setClaimSummary] = useState<ClaimSummary>({
		total: 0,
		absorbed: 0,
		pending: 0,
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
				setFetchedEvents((data.events as ProfileEvent[]) ?? []);
				setFetchedEdits((data.edits as SilentEdit[]) ?? []);
				setClaimSummary(
					(data.claimSummary as ClaimSummary) ?? {
						total: 0,
						absorbed: 0,
						pending: 0,
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

	// Filter snapshots by vertical — memoized, stable across day changes
	const filtered = useMemo(
		() => snapshots.filter((s) => s.vertical === vertical),
		[snapshots, vertical],
	);

	// Interpolate current snapshot
	const currentSnapshot = useMemo(() => {
		if (filtered.length === 0) return null;
		const nearest = nearestSnapshots(filtered, currentDay);
		if (!nearest) return null;
		return interpolate(nearest.a, nearest.b, currentDay);
	}, [filtered, currentDay]);

	// Day-0 baseline for delta computation
	const baseline = useMemo(
		() => filtered.find((s) => s.day === 0) ?? null,
		[filtered],
	);

	// Panel median values from prop
	const panelMedianOrig = panelMedian.orig;
	const panelMedianVal = panelMedian.val;

	// Play/pause animation
	useEffect(() => {
		if (!playing) {
			if (timerRef.current) clearInterval(timerRef.current);
			timerRef.current = null;
			return;
		}
		timerRef.current = setInterval(() => {
			startTransition(() => {
				setCurrentDay((prev) => {
					const next = prev + ANIMATION_SPEED;
					if (next >= DAY_MAX) {
						setPlaying(false);
						return DAY_MAX;
					}
					return next;
				});
			});
		}, ANIMATION_INTERVAL);
		return () => {
			if (timerRef.current) clearInterval(timerRef.current);
		};
	}, [playing]);

	const handleSlider = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
		setPlaying(false);
		setCurrentDay(Number(e.target.value));
	}, []);

	const togglePlay = useCallback(() => {
		setPlaying((p) => !p);
	}, []);

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
			{/* Page header */}
			<div className="flex items-center gap-3">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					{source.name}
				</h1>
			</div>
			<p className="-mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
				Tier {source.tier} &middot; {source.domain}
			</p>

			{/* Vertical picker pills */}
			<VerticalPills vertical={vertical} onChange={setVertical} />

			{/* Stat panel + Radar chart row */}
			<div className={`grid gap-6 ${"lg:grid-cols-[280px_1fr]"}`}>
				<StatPanel
					snapshot={currentSnapshot}
					baseline={baseline}
					medianOrig={panelMedianOrig}
					medianVal={panelMedianVal}
				/>
				<RadarChart
					snapshot={currentSnapshot}
					baseline={baseline}
					tierAvg={tierAvg}
				/>
			</div>

			{/* Sparklines */}
			<SparklineGrid
				snapshots={filtered}
				currentDay={Math.round(currentDay)}
				currentSnapshot={currentSnapshot}
			/>

			{/* Vf Trend Chart */}
			<VfTrendChart snapshots={filtered} currentDay={Math.round(currentDay)} />

			{/* Outlier waterfall */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
				<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-3">
					Claim Flow
				</h2>
				{claimSummary.total > 0 ? (
					<div className="space-y-2">
						<div className="flex items-center gap-3">
							<span className="w-24 font-mono text-[0.78rem] text-[var(--nn-text-dim)]">
								Absorbed
							</span>
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
						<p className="font-mono text-[0.72rem] text-[var(--nn-text-dim)] pt-1">
							{claimSummary.total} claims originated by this source
						</p>
					</div>
				) : (
					<p className="text-[var(--nn-text-dim)] text-[0.85rem]">
						No claims attributed.
					</p>
				)}
			</div>

			{/* Day scrubber */}
			<DayScrubber
				currentDay={currentDay}
				playing={playing}
				events={fetchedEvents}
				onSlider={handleSlider}
				onTogglePlay={togglePlay}
			/>

			{/* Silent Edit Log */}
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
	// Apply polarity inversion to the three "lower is better" dimensions
	const toRadarValues = (s: DailySnapshot | null): number[] | undefined => {
		if (!s) return undefined;
		const vals = DIMENSIONS.map((d) => {
			const v = s[d.key] as number | null;
			if (v == null) return null;
			return INVERTED_DIMS.has(d.key) ? 100 - v : v;
		});
		// ponytail: skip if any dimension is null (old snapshots pre-wiring)
		if (vals.some((v) => v == null)) return undefined;
		return vals as number[];
	};

	const curVal = toRadarValues(snapshot);
	const baseVal = toRadarValues(baseline);

	const hasData = curVal != null;

	const data = {
		labels: DIMENSIONS.map((d) => d.label),
		datasets: [
			{
				label: "Current",
				data: curVal ?? [],
				borderColor: "var(--nn-teal)",
				backgroundColor: "rgba(94,189,142,0.13)",
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
							data: tierAvg.map((v, i) =>
								INVERTED_DIMS.has(DIMENSIONS[i].key) ? 100 - v : v,
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
					color: "var(--nn-text-dim)",
					font: { size: 9 },
				},
				pointLabels: {
					color: "var(--nn-text-dim)",
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
						const dim = DIMENSIONS[ctx.dataIndex];
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
			<div className="h-[340px]">
				<Radar data={data} options={options} />
			</div>
		</div>
	);
}

function SparklineGrid({
	snapshots,
	currentDay,
	currentSnapshot,
}: {
	snapshots: DailySnapshot[];
	currentDay: number;
	currentSnapshot: DailySnapshot | null;
}) {
	// Build sparkline points for each dimension — trailing 30 days from currentDay
	const sparkData = useMemo(() => {
		if (snapshots.length === 0) return null;
		const sorted = [...snapshots].sort((a, b) => a.day - b.day);
		const startDay = Math.max(0, currentDay - SPARKLINE_WINDOW);
		const window = sorted.filter(
			(s) => s.day >= startDay && s.day <= currentDay,
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
	}, [snapshots, currentDay]);

	// Use parent's interpolated currentSnapshot instead of re-computing closest (review-03 M08)
	const currentVal = currentSnapshot;

	return (
		<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
			<h2 className="mb-3 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
				30-Day Trends
			</h2>
			<div className="grid grid-cols-2 gap-x-6 gap-y-2">
				{DIMENSIONS.map((dim) => {
					const spark = sparkData?.find((s) => s.dim.key === dim.key);
					const val = currentVal?.[dim.key] as number | undefined;
					return (
						<div key={dim.key} className="flex items-center gap-2">
							<span className="w-28 flex-shrink-0 text-right font-mono text-[0.66rem] text-[var(--nn-text-dim)]">
								{dim.label}
							</span>
							<svg
								viewBox="0 0 30 20"
								className="h-5 flex-1"
								role="img"
								aria-label={`${dim.label} trend`}
							>
								{spark?.points && (
									<polyline
										fill="none"
										stroke="var(--nn-slate)"
										strokeOpacity={0.7}
										strokeWidth={1.2}
										vectorEffect="non-scaling-stroke"
										points={spark.points}
									/>
								)}
							</svg>
							<span className="w-8 flex-shrink-0 text-right font-mono text-[0.7rem] tabular-nums text-[var(--nn-text)]">
								{val != null ? Math.round(val) : "—"}
							</span>
						</div>
					);
				})}
			</div>
		</div>
	);
}

function DayScrubber({
	currentDay,
	playing,
	events,
	onSlider,
	onTogglePlay,
}: {
	currentDay: number;
	playing: boolean;
	events: ProfileEvent[];
	onSlider: (e: React.ChangeEvent<HTMLInputElement>) => void;
	onTogglePlay: () => void;
}) {
	// Nearest event at or before current day
	const nearestEvent = useMemo(() => {
		const passed = events.filter((e) => e.day <= currentDay + 0.5);
		return passed.length > 0 ? passed[passed.length - 1] : null;
	}, [events, currentDay]);

	return (
		<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
			<div className="flex items-center gap-3">
				<button
					type="button"
					onClick={onTogglePlay}
					aria-label={playing ? "Pause" : "Play"}
					className="flex items-center gap-1 rounded-md px-3 py-2 font-heading text-[0.82rem] font-bold text-[var(--nn-teal)] transition-colors hover:bg-[var(--nn-teal)]/10"
					style={{
						backgroundColor: playing ? "var(--nn-teal)" : undefined,
						color: playing ? "#04140c" : undefined,
					}}
				>
					{playing ? (
						<Pause className="h-4 w-4" />
					) : (
						<Play className="h-4 w-4" />
					)}
					{playing ? "Pause" : "Play"}
				</button>
				<input
					type="range"
					min={0}
					max={DAY_MAX}
					step={1}
					value={Math.round(currentDay)}
					onChange={onSlider}
					className="flex-1 accent-[var(--nn-teal)]"
					style={{ accentColor: "var(--nn-teal)" }}
					aria-label="Day scrubber"
				/>
				<span className="w-16 flex-shrink-0 text-right font-mono text-[0.82rem] tabular-nums text-[var(--nn-text)]">
					Day {Math.round(currentDay)}
				</span>
			</div>

			{/* Event markers */}
			{events.length > 0 && (
				<div className="relative mt-2 h-5">
					<div className="absolute inset-x-0 top-2 h-px bg-[var(--nn-border)]" />
					{events.map((ev) => {
						const pct = (ev.day / DAY_MAX) * 100;
						const passed = ev.day <= currentDay + 0.5;
						const color =
							ev.type === "CLAIM_ABSORBED"
								? "var(--nn-teal)"
								: "var(--nn-amber)";
						return (
							<button
								key={`${ev.day}-${ev.type}`}
								type="button"
								className="absolute top-1 h-3 w-3 -translate-x-1/2 rounded-full border-2 transition-colors"
								style={{
									left: `${pct}%`,
									borderColor: color,
									backgroundColor: passed ? color : "transparent",
								}}
								onClick={() => {
									onSlider({
										target: { value: String(ev.day) },
									} as React.ChangeEvent<HTMLInputElement>);
								}}
								aria-label={`Day ${ev.day}: ${ev.title}`}
							/>
						);
					})}
				</div>
			)}

			{/* Event card */}
			<div className="mt-3 min-h-[52px] rounded-lg border border-[var(--nn-border)] bg-[var(--nn-surface2)] px-3.5 py-3 text-[0.78rem] text-[var(--nn-text-dim)]">
				{nearestEvent ? (
					<>
						<span className="mr-2 font-mono text-[0.68rem] text-[var(--nn-amber)]">
							DAY {nearestEvent.day}
						</span>
						<b className="text-[var(--nn-text)]">{nearestEvent.title}.</b>{" "}
						{nearestEvent.detail}
					</>
				) : (
					"Drag the slider, hit play, or click a marker to jump to a moment."
				)}
			</div>
		</div>
	);
}

export default SourceProfilePage;
