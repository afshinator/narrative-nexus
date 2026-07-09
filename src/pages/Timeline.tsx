import { useEffect, useState } from "react";
import { useParams } from "react-router";

interface Claim {
	id: number;
	text: string;
	state: string;
	absorbed_at: string | null;
	first_seen_at: string;
	created_at: string;
}

interface SourceGroup {
	domain: string;
	tier: number;
	claims: Claim[];
}

interface TimelineData {
	cluster: { id: number; title: string };
	sources: SourceGroup[];
}

// ponytail: compute left% for claim card based on first_seen_at
function positionPercent(
	firstSeenAt: string,
	rangeStart: number,
	rangeMs: number,
): number {
	if (rangeMs === 0) return 0;
	const ts = new Date(firstSeenAt).getTime();
	return ((ts - rangeStart) / rangeMs) * 100;
}

export default function TimelinePage() {
	const { clusterId } = useParams<{ clusterId: string }>();
	const [data, setData] = useState<TimelineData | null>(null);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let cancelled = false;
		fetch(`/api/timeline/${clusterId}`)
			.then((r) => {
				if (!r.ok)
					throw new Error(
						r.status === 404 ? "Cluster not found" : "Failed to load",
					);
				return r.json();
			})
			.then((d: TimelineData) => {
				if (!cancelled) setData(d);
			})
			.catch((e: Error) => {
				if (!cancelled) setError(e.message);
			});
		return () => {
			cancelled = true;
		};
	}, [clusterId]);

	if (error) {
		return (
			<div className="mx-auto max-w-[1340px] space-y-6">
				<p className="font-mono text-[0.75rem] uppercase tracking-[0.12em] text-[var(--nn-text-dim)]">
					Timeline
				</p>
				<h1 className="font-heading text-[2rem] font-bold text-[var(--nn-text)]">
					Timeline
				</h1>
				<p className="text-[var(--nn-text-dim)]">{error}</p>
			</div>
		);
	}

	if (!data) {
		return (
			<div className="mx-auto max-w-[1340px] space-y-6">
				<p className="font-mono text-[0.75rem] uppercase tracking-[0.12em] text-[var(--nn-text-dim)]">
					Timeline
				</p>
				<h1 className="font-heading text-[2rem] font-bold text-[var(--nn-text)]">
					Timeline
				</h1>
				<p className="text-[var(--nn-text-dim)]">Loading…</p>
			</div>
		);
	}

	// ponytail: compute time range for positioning — filter NaN from empty first_seen_at
	const allTimes = data.sources.flatMap((s) =>
		s.claims
			.map((c) => new Date(c.first_seen_at).getTime())
			.filter((t) => !Number.isNaN(t)),
	);

	// ponytail: cluster with no claims — show empty state
	if (allTimes.length === 0) {
		return (
			<div className="mx-auto max-w-[1340px] space-y-6">
				<div className="flex items-center gap-3 mb-1.5">
					<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
						Timeline
					</h1>
					<span className="font-mono text-[0.8rem] text-[var(--nn-text-dim)]">
						{data.cluster.title}
					</span>
				</div>
				<p className="text-[var(--nn-text-dim)] text-[0.85rem]">
					No claims in this cluster.
				</p>
			</div>
		);
	}

	const rangeStart = Math.min(...allTimes);
	const rangeEnd = Math.max(...allTimes);
	const rangeMs = rangeEnd - rangeStart || 1;

	// UX39: only label days that have claims — not every calendar day
	const claimDates = [
		...new Set(
			data.sources.flatMap((s) =>
				s.claims.map((c) => c.first_seen_at.split("T")[0]),
			),
		),
	].sort();
	const days = claimDates.map((d) => new Date(`${d}T00:00:00`));

	// M2: single-day range — timeline unavailable
	if (days.length <= 1) {
		return (
			<div className="mx-auto max-w-[1340px] space-y-6">
				<div className="flex items-center gap-3 mb-1.5">
					<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">Timeline</h1>
					<span className="font-mono text-[0.8rem] text-[var(--nn-text-dim)]">{data.cluster.title}</span>
				</div>
				<p className="text-[var(--nn-text-dim)] text-[0.85rem]">
					Timeline unavailable for this cluster — claims span a single day, insufficient for temporal visualization.
				</p>
			</div>
		);
	}

	// UX39: global claim legend — numbered chronologically
	const allClaims = data.sources
		.flatMap((s) => s.claims.map((c) => ({ ...c, _source: s.domain })))
		.sort(
			(a, b) =>
				new Date(a.first_seen_at).getTime() - new Date(b.first_seen_at).getTime(),
		);

	// Build per-source claim map with global index for dot rendering
	const claimIndex = new Map<number, number>(); // claim.id -> global index
	allClaims.forEach((c, i) => claimIndex.set(c.id, i + 1));

	// Within each source, compute dot offset for same-date claims
	function claimDotStyle(
		claim: Claim,
		sourceGroup: SourceGroup,
	): { left: number; top: number } {
		const pct = positionPercent(claim.first_seen_at, rangeStart, rangeMs);
		const sameDay = sourceGroup.claims.filter(
			(c) =>
				c.first_seen_at.split("T")[0] === claim.first_seen_at.split("T")[0],
		);
		const idx = sameDay.findIndex((c) => c.id === claim.id);
		return {
			left: Math.max(0, Math.min(100, pct)),
			top: 4 + idx * 22,
		};
	}

	return (
		<div className="mx-auto max-w-[1340px] space-y-6">
			{/* UX15 title block */}
			<p className="font-mono text-[0.75rem] uppercase tracking-[0.12em] text-[var(--nn-text-dim)]">
				Timeline
			</p>
			{/* Header */}
			<div className="flex items-center gap-3 mb-1.5">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					{data.cluster.title}
				</h1>
			</div>
			{/* K3: narrative description */}
			<p className="-mt-2 font-sans text-[0.85rem] leading-relaxed text-[var(--nn-text-dim)]">
				One story, reconstructed from {data.sources.length} sources —{" "}
				{data.sources.reduce((sum, s) => sum + s.claims.length, 0)} extracted claims over {days.length} day{days.length !== 1 ? "s" : ""}.
			</p>

			{/* F5: Single-source cluster banner */}
			{data.sources.length === 1 && (
				<div className="rounded-[10px] border border-[var(--nn-border)] bg-[var(--nn-surface)] px-4 py-3 font-sans text-[0.85rem] text-[var(--nn-text-dim)]">
					<span className="font-semibold text-[var(--nn-text)]">Single-source cluster</span>
					{" "}
					— no cross-source propagation to visualize. This source&apos;s
					claims are shown alone. When other outlets report the same claim,
					propagation lines will appear connecting sources across time.
				</div>
			)}

			{/* Day header bar */}
			<p className="mb-2 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
				Each marker shows when a source first reported a claim. Claims from different sources on related stories are grouped vertically.
			</p>
			<div
				className="relative mb-2 ml-[180px] h-6"
				style={{ width: "calc(100% - 180px)" }}
			>
				{days.map((d) => {
					const pct = ((d.getTime() - rangeStart) / rangeMs) * 100;
					return (
						<span
							key={d.toISOString()}
							className="absolute font-mono text-[0.75rem] text-[var(--nn-text-dim)]"
							style={{
								left: `${Math.max(0, pct)}%`,
								transform: "translateX(-50%)",
							}}
						>
							{d.toLocaleDateString("en-US", {
								month: "short",
								day: "numeric",
							})}
						</span>
					);
				})}
			</div>

			{/* Source rows */}
			{data.sources.map((source) => (
				<div
					key={source.domain}
					className="flex items-start gap-3 py-2 border-b border-[var(--nn-border)] last:border-b-0"
				>
					{/* Source label */}
					<div className="w-[168px] shrink-0 pt-0.5 text-right">
						<span className="block font-semibold text-[0.85rem] text-[var(--nn-text)]">
							{source.domain}
						</span>
						<span className="font-mono text-[0.75rem] text-[var(--nn-text-dim)]">
							Tier {source.tier} &middot; {source.claims.length} claims
						</span>
					</div>

					{/* Claim markers — numbered dots positioned horizontally */}
					<div
						className="relative flex-1"
						style={{
							minHeight: Math.max(
								40,
								(() => {
									const maxSameDay = Math.max(
										...source.claims.reduce<Map<string, number>>((acc, c) => {
											const d = c.first_seen_at.split("T")[0];
											acc.set(d, (acc.get(d) ?? 0) + 1);
											return acc;
										}, new Map()).values(),
									);
									return (maxSameDay - 1) * 22 + 24;
								})(),
							),
						}}
					>
						<div className="relative" style={{ width: "100%", height: "100%" }}>
							{source.claims.map((claim) => {
								const { left, top } = claimDotStyle(claim, source);
								const absorbed = claim.state === "CONSENSUS_ABSORBED";
								const idx = claimIndex.get(claim.id) ?? 0;
								return (
									<span
										key={claim.id}
										title={`#${idx}: ${claim.text}`}
										className={`absolute inline-flex size-5 items-center justify-center rounded-full font-mono text-[0.75rem] font-bold leading-none cursor-default ${
											absorbed
												? "bg-[var(--nn-teal)] text-white"
												: "bg-[var(--nn-surface2)] text-[var(--nn-text)]"
										}`}
										style={{
											left: `${left}%`,
											top: `${top}px`,
											transform: "translateX(-50%)",
										}}
									>
										{idx}
									</span>
								);
							})}
						</div>
					</div>
				</div>
			))}

			{/* UX39: Claim legend — numbered, chronologically sorted */}
			<div className="mt-4 rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
				<h2 className="mb-3 font-heading text-[1.1rem] font-bold text-[var(--nn-text)]">
					Claims Legend
				</h2>
				<div className="space-y-2">
					{allClaims.map((claim, i) => {
						const absorbed = claim.state === "CONSENSUS_ABSORBED";
						return (
							<div key={claim.id} className="flex items-start gap-3">
								<span
									className={`inline-flex size-5 shrink-0 items-center justify-center rounded-full font-mono text-[0.75rem] font-bold leading-none ${
										absorbed
											? "bg-[var(--nn-teal)] text-white"
											: "bg-[var(--nn-surface2)] text-[var(--nn-text)]"
									}`}
								>
									{i + 1}
								</span>
								<div className="min-w-0">
									<span className="font-sans text-[0.82rem] leading-relaxed text-[var(--nn-text)]">
										{claim.text}
									</span>
									<span className="ml-2 font-mono text-[0.75rem] text-[var(--nn-text-dim)]">
										{claim._source}
									</span>
									<span className="ml-1 font-mono text-[0.75rem] text-[var(--nn-text-dim)]">
										{claim.first_seen_at?.slice(0, 10)}
									</span>
								</div>
							</div>
						);
					})}
				</div>
			</div>
		</div>
	);
}
