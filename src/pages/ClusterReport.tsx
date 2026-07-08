import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

interface SourceRow {
	domain: string;
	tier: number;
	claims: number;
	absorbed: number;
	pending: number;
}

interface ClaimRow {
	id: number;
	text: string;
	state: string;
	absorbed_at: string | null;
	created_at: string;
	domains: string[];
}

interface ReportData {
	cluster: { id: number; title: string; vertical: string };
	summary: {
		totalClaims: number;
		absorbed: number;
		pending: number;
		sourceCount: number;
		articleCount?: number;
		coverageStart?: string | null;
		coverageEnd?: string | null;
		topSourceNames?: string[];
		poolSize?: number;
		poolParticipating?: number;
		poolPct?: number;
		abstainingNames?: string[];
		distinctDays?: number;
		emptyDateCount?: number;
	};
	sources: SourceRow[];
	claims: ClaimRow[];
}

export default function ClusterReportPage() {
	const { clusterId } = useParams<{ clusterId: string }>();
	const [data, setData] = useState<ReportData | null>(null);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let cancelled = false;
		fetch(`/api/clusters/${clusterId}/report`)
			.then((r) => {
				if (!r.ok)
					throw new Error(
						r.status === 404 ? "Cluster not found" : "Failed to load",
					);
				return r.json();
			})
			.then((d: ReportData) => {
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
					Cluster Report
				</p>
				<h1 className="font-heading text-[2rem] font-bold text-[var(--nn-text)]">
					Cluster Report
				</h1>
				<p className="text-[var(--nn-text-dim)]">{error}</p>
			</div>
		);
	}

	if (!data) {
		return (
			<div className="mx-auto max-w-[1340px] space-y-6">
				<p className="font-mono text-[0.75rem] uppercase tracking-[0.12em] text-[var(--nn-text-dim)]">
					Cluster Report
				</p>
				<h1 className="font-heading text-[2rem] font-bold text-[var(--nn-text)]">
					Cluster Report
				</h1>
				<p className="text-[var(--nn-text-dim)]">Loading…</p>
			</div>
		);
	}

	return (
		<div className="mx-auto max-w-[1340px] space-y-6">
			{/* UX15 title block */}
			<p className="font-mono text-[0.75rem] uppercase tracking-[0.12em] text-[var(--nn-text-dim)]">
				Cluster Report
			</p>
			{/* Header */}
			<div className="flex items-center gap-3 mb-1.5">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					{data.cluster.title}
				</h1>
			</div>
			{/* K3: narrative description — explains what the page is */}
			<p className="-mt-2 font-sans text-[0.85rem] leading-relaxed text-[var(--nn-text-dim)]">
				One story, reconstructed from {data.sources.length} sources — {data.summary.totalClaims} extracted claims, {data.summary.absorbed} absorbed into consensus.
				{data.summary.distinctDays != null && data.summary.distinctDays > 1
				 && data.summary.emptyDateCount === 0 && (
					<>{" "}<Link to={`/timeline/${data.cluster.id}`} className="font-medium text-[var(--nn-navy)] hover:underline">
						View timeline →
					</Link></>
				)}
			</p>

			{/* ── Consensus Summary + Coverage ── */}
			<div className="grid gap-4 lg:grid-cols-[1fr_280px]">
				<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
				<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-1">
					Consensus Summary
				</h2>
				<p className="mb-3 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
					How many claims are in this cluster, from how many sources, and how many reached consensus
				</p>
				<div className="flex flex-wrap gap-x-8 gap-y-1 font-mono text-[0.85rem]">
					<span>
						<span className="text-[var(--nn-text)]">
							{data.summary.totalClaims}
						</span>{" "}
						<span className="text-[var(--nn-text-dim)]">claims</span>
					</span>
					<span>
						<span className="text-[var(--nn-text)]">
							{data.summary.sourceCount}
						</span>{" "}
						<span className="text-[var(--nn-text-dim)]">sources</span>
					</span>
					<span>
						<span className="text-[var(--nn-teal)]">
							{data.summary.absorbed}
						</span>{" "}
						<span className="text-[var(--nn-text-dim)]">absorbed</span>
					</span>
					<span>
						<span className="text-[var(--nn-navy)]">
							{data.summary.pending}
						</span>{" "}
						<span className="text-[var(--nn-text-dim)]">pending</span>
					</span>
				</div>
			{data.summary.absorbed > 0 && (
						<>
							<p className="font-sans text-[0.85rem] leading-relaxed text-[var(--nn-text)]">
								<strong>Two independent corroborating sources — cross-source convergent,
								not self-validating.</strong>{" "}
								{data.summary.topSourceNames && data.summary.topSourceNames.length > 0
									? `Sourced from ${data.summary.topSourceNames.join(" + ")}.`
									: ""}
							</p>
							{data.summary.poolSize != null && data.summary.poolSize > 0 && (
								<p className="mt-0.5 font-mono text-[0.75rem] text-[var(--nn-text-dim)]">
									{data.summary.poolParticipating} of {data.summary.poolSize} pool sources
									{data.summary.abstainingNames && data.summary.abstainingNames.length > 0
										? ` (${data.summary.abstainingNames.join(", ")} abstained)`
										: ""}{" "}
									&middot; {data.summary.poolPct}% &ge; 65% geopolitics threshold
									&middot; claim variants matched at &ge;0.85
								</p>
							)}
						</>
					)}
				</div>

				{/* UX32: Coverage stat block */}
				<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
					<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-1">
						Coverage
					</h2>
					<p className="mb-3 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
						How long and wide the collection ran
					</p>
					{(() => {
						const start = data.summary.coverageStart;
						const end = data.summary.coverageEnd;
						const spanDays = start && end
							? Math.round((new Date(end).getTime() - new Date(start).getTime()) / 86400000)
							: null;
						const THRESHOLD = 30;
						const tempo = spanDays != null
							? (spanDays >= THRESHOLD ? `${spanDays}-day arc` : `${spanDays}-day surge`)
							: null;
						const fmt = (iso: string | null | undefined) => {
							if (!iso) return "—";
							const d = new Date(iso);
							return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
						};
						const startFmt = fmt(start);
						const endFmt = fmt(end);
						return (
							<div className="space-y-3 font-mono text-[0.75rem]">
								<p className="text-[var(--nn-text)]">
									<span className="font-semibold">{tempo ?? "—"}</span>
								</p>
								<p className="text-[var(--nn-text-dim)]">
									{startFmt} – {endFmt}
									{spanDays != null && <span className="ml-1">({spanDays} days)</span>}
								</p>
								<div className="space-y-0.5">
									<p>
										<span className="text-[var(--nn-text)]">{data.summary.articleCount ?? "—"}</span>
										<span className="text-[var(--nn-text-dim)]"> articles</span>
									</p>
									<p>
										<span className="text-[var(--nn-text)]">{data.summary.totalClaims}</span>
										<span className="text-[var(--nn-text-dim)]"> claims</span>
									</p>
									<p>
										<span className="text-[var(--nn-text)]">{data.summary.sourceCount}</span>
										<span className="text-[var(--nn-text-dim)]"> sources</span>
									</p>
								</div>
							</div>
						);
					})()}
				</div>
			</div>

			{/* F4c: Honest framing when no claims absorbed yet */}
			{data.summary.absorbed === 0 && (
				<div className="rounded-[10px] border border-[var(--nn-border)] bg-[var(--nn-surface)] px-4 py-3 font-sans text-[0.85rem] text-[var(--nn-text-dim)]">
					<span className="font-semibold text-[var(--nn-text)]">Why 0 absorbed?</span>
					{" "}
					This cluster contains {data.summary.totalClaims} claims from{" "}
					{data.summary.sourceCount} sources. None have cleared cross-source
					corroboration yet (≥2 Tier 1–2 sources at the vertical&apos;s percentage
					threshold). Claims remain pending while the system waits for additional
					reporting. The Timeline and source table show which outlets have
					reported each claim.
				</div>
			)}

			{/* ── Source Breakdown + Claim List ── */}
			<div className="grid gap-6 lg:grid-cols-[280px_1fr]">
				{/* Source breakdown (was: distortion matrix) */}
				<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
					<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-1">
						Source Breakdown
					</h2>
					<p className="mb-3 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
						Which sources reported claims in this cluster, and how many each contributed
					</p>
					<div className="overflow-x-auto">
						<table className="w-full border-collapse text-[0.82rem]">
							<thead>
								<tr>
									<th className="px-1.5 py-1.5 text-left font-mono text-[0.75rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b border-[var(--nn-border)]">
										Source
									</th>
									<th className="px-1.5 py-1.5 text-right font-mono text-[0.75rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b border-[var(--nn-border)]">
										Claims
									</th>
								</tr>
							</thead>
							<tbody>
								{data.sources.map((s) => (
									<tr
										key={s.domain}
										className="border-b border-[var(--nn-border)] last:border-b-0"
									>
										<td className="px-1.5 py-1.5">
											<span className="text-[var(--nn-text)]">{s.domain}</span>
											<span className="ml-1.5 font-mono text-[0.75rem] text-[var(--nn-text-dim)]">
												T{s.tier}
											</span>
										</td>
										<td className="px-1.5 py-1.5 text-right font-mono tabular-nums text-[var(--nn-text)]">
											{s.claims}
											<span className="ml-1 text-[0.75rem] text-[var(--nn-text-dim)]">
												{s.absorbed > 0 ? ` (${s.absorbed}A)` : ""}
												{s.pending > 0 ? ` (${s.pending}P)` : ""}
											</span>
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				</div>

				{/* Claim list */}
				<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
					<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-1">
						Claims
					</h2>
					<p className="mb-3 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
						Every claim in this cluster, its current state, and which sources reported it
					</p>
					<div className="max-h-[60vh] overflow-y-auto">
						<table className="w-full border-collapse text-[0.82rem]">
							<thead>
								<tr>
									<th className="px-1.5 py-1.5 text-left font-mono text-[0.75rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b border-[var(--nn-border)]">
										Source
									</th>
									<th className="px-1.5 py-1.5 text-left font-mono text-[0.75rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b border-[var(--nn-border)]">
										Claim
									</th>
									<th className="px-1.5 py-1.5 text-right font-mono text-[0.75rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b border-[var(--nn-border)]">
										State
									</th>
								</tr>
							</thead>
							<tbody>
								{(() => {
									const absorbed = data.claims.filter((c) => c.state === "CONSENSUS_ABSORBED");
									const rest = data.claims.filter((c) => c.state !== "CONSENSUS_ABSORBED");
									const renderClaim = (c: ClaimRow, _i: number, isAbsorbed: boolean) => (
										<tr
											key={c.id}
											className={`border-b border-[var(--nn-border)] last:border-b-0 ${isAbsorbed ? "bg-[var(--nn-teal)]/5" : ""}`}
										>
											<td className="px-1.5 py-1.5 font-mono text-[0.75rem] text-[var(--nn-text-dim)] whitespace-nowrap">
												{c.domains.join(", ")}
											</td>
											<td className="px-1.5 py-1.5 text-[var(--nn-text)] max-w-[500px] truncate" title={c.text}>
												{isAbsorbed ? <strong>{c.text}</strong> : c.text}
											</td>
											<td className="px-1.5 py-1.5 text-right">
												<span className={`font-mono text-[0.75rem] ${isAbsorbed ? "text-[var(--nn-teal)] font-semibold" : c.state === "UNRESOLVED" ? "text-[var(--nn-slate)]" : "text-[var(--nn-navy)]"}`}>
													{c.state === "CONSENSUS_ABSORBED" ? "absorbed" : c.state === "UNRESOLVED" ? "unresolved" : "pending"}
												</span>
											</td>
										</tr>
									);
									return (
										<>
											{absorbed.map((c, i) => renderClaim(c, i, true))}
											{rest.length > 0 && (
												<>
													<tr><td colSpan={3} className="pt-4 pb-1 font-sans text-[0.75rem] font-semibold text-[var(--nn-text-dim)]">
														Awaiting cross-source corroboration &mdash; {data.summary.pending + (data.summary.totalClaims - data.summary.absorbed - data.summary.pending)} claims pending or unresolved
													</td></tr>
													{rest.map((c, i) => renderClaim(c, i, false))}
												</>
											)}
										</>
									);
								})()}
							</tbody>
						</table>
					</div>
				</div>
			</div>

			{/* ── Forensic Analysis ── */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
				<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-3">
					Forensic Analysis
				</h2>
				<p className="text-[var(--nn-text-dim)] text-[0.85rem]">
					Convergence-type data is not yet computed by Agent 3 (consensus
					alignment). Cross-source convergent and self-consistent
					classifications will appear here when available.
				</p>
			</div>
		</div>
	);
}
