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
function positionPercent(firstSeenAt: string, rangeStart: number, rangeMs: number): number {
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
				if (!r.ok) throw new Error(r.status === 404 ? "Cluster not found" : "Failed to load");
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
				<h1 className="font-heading text-[2rem] font-bold text-[var(--nn-text)]">Timeline</h1>
				<p className="text-[var(--nn-text-dim)]">{error}</p>
			</div>
		);
	}

	if (!data) {
		return (
			<div className="mx-auto max-w-[1340px] space-y-6">
				<h1 className="font-heading text-[2rem] font-bold text-[var(--nn-text)]">Timeline</h1>
				<p className="text-[var(--nn-text-dim)]">Loading…</p>
			</div>
		);
	}

	// ponytail: compute time range for positioning
	const allTimes = data.sources.flatMap((s) =>
		s.claims.map((c) => new Date(c.first_seen_at).getTime()),
	);

	// ponytail: cluster with no claims — show empty state
	if (allTimes.length === 0) {
		return (
			<div className="mx-auto max-w-[1340px] space-y-6">
				{/* Header */}
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
	// Day markers (midnight boundaries)
	const startDay = new Date(rangeStart);
	startDay.setHours(0, 0, 0, 0);
	const days: Date[] = [];
	for (let d = new Date(startDay); d.getTime() <= rangeEnd; d.setDate(d.getDate() + 1)) {
		days.push(new Date(d));
	}

	return (
		<div className="mx-auto max-w-[1340px] space-y-6">
			{/* Header */}
			<div className="flex items-center gap-3 mb-1.5">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					Timeline
				</h1>
				<span className="font-mono text-[0.8rem] text-[var(--nn-text-dim)]">
					{data.cluster.title}
				</span>
			</div>
			<p className="-mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
				{data.sources.length} sources &middot;{" "}
				{data.sources.reduce((sum, s) => sum + s.claims.length, 0)} claims &middot;{" "}
				{days.length} day{days.length !== 1 ? "s" : ""}
			</p>

			{/* Day header bar */}
			<div
				className="relative mb-2 ml-[180px] h-6"
				style={{ width: "calc(100% - 180px)" }}
			>
				{days.map((d) => {
					const pct = ((d.getTime() - rangeStart) / rangeMs) * 100;
					return (
						<span
							key={d.toISOString()}
							className="absolute font-mono text-[0.7rem] text-[var(--nn-text-dim)]"
							style={{ left: `${Math.max(0, pct)}%`, transform: "translateX(-50%)" }}
						>
							{d.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
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
						<span className="font-mono text-[0.72rem] text-[var(--nn-text-dim)]">
							Tier {source.tier} &middot; {source.claims.length} claims
						</span>
					</div>

					{/* Claim cards — positioned horizontally */}
					<div className="relative flex-1 overflow-x-auto" style={{ height: 48 }}>
						<div className="relative" style={{ width: "100%", height: 40 }}>
							{source.claims.map((claim) => {
								const pct = positionPercent(
									claim.first_seen_at,
									rangeStart,
									rangeMs,
								);
								const absorbed = claim.state === "CONSENSUS_ABSORBED";
								return (
									<span
										key={claim.id}
										title={claim.text}
										className={`absolute top-1 block h-7 max-w-[140px] cursor-default overflow-hidden text-ellipsis whitespace-nowrap rounded px-2 py-0.5 font-mono text-[0.68rem] leading-relaxed ${
											absorbed
												? "bg-[var(--nn-teal)]/15 text-[var(--nn-teal)]"
												: "bg-[var(--nn-surface2)] text-[var(--nn-text-dim)]"
										}`}
										style={{ left: `${Math.max(0, Math.min(100, pct))}%` }}
									>
										{claim.text}
									</span>
								);
							})}
						</div>
					</div>
				</div>
			))}

			{/* Day marker lines */}
			<div className="hidden">{/* ponytail: visual check first, add lines later */}</div>
		</div>
	);
}
