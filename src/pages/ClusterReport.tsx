import { useEffect, useState } from "react";
import { useParams } from "react-router";

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
	domain: string;
}

interface ReportData {
	cluster: { id: number; title: string; vertical: string };
	summary: {
		totalClaims: number;
		absorbed: number;
		pending: number;
		sourceCount: number;
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
				<h1 className="font-heading text-[2rem] font-bold text-[var(--nn-text)]">
					Cluster Report
				</h1>
				<p className="text-[var(--nn-text-dim)]">Loading…</p>
			</div>
		);
	}

	return (
		<div className="mx-auto max-w-[1340px] space-y-6">
			{/* Header */}
			<div className="flex items-center gap-3 mb-1.5">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					Cluster Report
				</h1>
				<span className="font-mono text-[0.8rem] text-[var(--nn-text-dim)]">
					{data.cluster.title}
				</span>
			</div>

			{/* ── Consensus Summary ── */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
				<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-3">
					Consensus Summary
				</h2>
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
					<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-3">
						Source Breakdown
					</h2>
					<div className="overflow-x-auto">
						<table className="w-full border-collapse text-[0.82rem]">
							<thead>
								<tr>
									<th className="px-1.5 py-1.5 text-left font-mono text-[0.68rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b border-[var(--nn-border)]">
										Source
									</th>
									<th className="px-1.5 py-1.5 text-right font-mono text-[0.68rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b border-[var(--nn-border)]">
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
											<span className="ml-1.5 font-mono text-[0.7rem] text-[var(--nn-text-dim)]">
												T{s.tier}
											</span>
										</td>
										<td className="px-1.5 py-1.5 text-right font-mono tabular-nums text-[var(--nn-text)]">
											{s.claims}
											<span className="ml-1 text-[0.7rem] text-[var(--nn-text-dim)]">
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
					<h2 className="font-heading text-[1.1rem] font-bold text-[var(--nn-text)] mb-3">
						Claims
					</h2>
					<div className="max-h-[60vh] overflow-y-auto">
						<table className="w-full border-collapse text-[0.82rem]">
							<thead>
								<tr>
									<th className="px-1.5 py-1.5 text-left font-mono text-[0.68rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b border-[var(--nn-border)]">
										Source
									</th>
									<th className="px-1.5 py-1.5 text-left font-mono text-[0.68rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b border-[var(--nn-border)]">
										Claim
									</th>
									<th className="px-1.5 py-1.5 text-right font-mono text-[0.68rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b border-[var(--nn-border)]">
										State
									</th>
								</tr>
							</thead>
							<tbody>
								{data.claims.map((c) => (
									<tr
										key={c.id}
										className="border-b border-[var(--nn-border)] last:border-b-0"
									>
										<td className="px-1.5 py-1.5 font-mono text-[0.72rem] text-[var(--nn-text-dim)] whitespace-nowrap">
											{c.domain}
										</td>
										<td
											className="px-1.5 py-1.5 text-[var(--nn-text)] max-w-[500px] truncate"
											title={c.text}
										>
											{c.text}
										</td>
										<td className="px-1.5 py-1.5 text-right">
											<span
												className={`font-mono text-[0.72rem] ${
													c.state === "CONSENSUS_ABSORBED"
														? "text-[var(--nn-teal)]"
														: "text-[var(--nn-navy)]"
												}`}
											>
												{c.state === "CONSENSUS_ABSORBED"
													? "absorbed"
													: "pending"}
											</span>
										</td>
									</tr>
								))}
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
