import { ArrowRight, Clock } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router";

interface StoryData {
	id: number;
	title: string;
	articleCount: number;
	claimCount: number;
	sourceCount: number;
	coverageStart: string | null;
	coverageEnd: string | null;
	spanDays: number | null;
	absorbedCount: number;
	absorbedTexts: string[];
	sources: string[];
	silentEdits: number;
	corrections: number;
	timeToConsensusMedian: number | null;
}

const CLUSTER_IDS = [966, 924];

async function fetchStory(id: number): Promise<StoryData> {
	const r = await fetch(`/api/clusters/${id}/report`);
	if (!r.ok) throw new Error(`Cluster ${id} not found`);
	const d = await r.json();
	const summary = d.summary;
	return {
		id: d.cluster.id,
		title: d.cluster.title,
		articleCount: summary.articleCount ?? 0,
		claimCount: summary.totalClaims,
		sourceCount: summary.sourceCount,
		coverageStart: summary.coverageStart,
		coverageEnd: summary.coverageEnd,
		spanDays: summary.coverageStart && summary.coverageEnd
			? Math.round(
					(new Date(summary.coverageEnd).getTime() -
						new Date(summary.coverageStart).getTime()) /
						86400000,
				)
			: null,
		absorbedCount: summary.absorbed,
		absorbedTexts: d.claims
			.filter((c: { state: string }) => c.state === "CONSENSUS_ABSORBED")
			.map((c: { text: string }) => c.text),
		sources: (d.sources as Array<{ domain: string }>).map((s) => s.domain),
		silentEdits: summary.silentEdits ?? 0,
		corrections: summary.corrections ?? 0,
		timeToConsensusMedian: summary.timeToConsensusDays ?? null,
	};
}

const THRESHOLD = 30;

function tempoLabel(days: number | null): string {
	if (days == null) return "—";
	return days >= THRESHOLD ? `${days}-day arc` : `${days}-day surge`;
}

function fmtDate(iso: string | null | undefined): string {
	if (!iso) return "—";
	const d = new Date(iso);
	return d.toLocaleDateString("en-US", {
		month: "short",
		day: "numeric",
		year: "numeric",
	});
}

export default function StoriesPage() {
	const [stories, setStories] = useState<StoryData[]>([]);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let cancelled = false;
		Promise.all(CLUSTER_IDS.map(fetchStory))
			.then((results) => {
				if (!cancelled) setStories(results);
			})
			.catch((e: Error) => {
				if (!cancelled) setError(e.message);
			});
		return () => {
			cancelled = true;
		};
	}, []);

	if (error) {
		return (
			<div className="mx-auto max-w-[1340px] space-y-6">
				<h1 className="font-heading text-[2rem] font-bold text-(--nn-text)">
					Stories
				</h1>
				<p className="text-(--nn-text-dim)">{error}</p>
			</div>
		);
	}

	if (stories.length === 0) {
		return (
			<div className="mx-auto max-w-[1340px] space-y-6">
				<h1 className="font-heading text-[2rem] font-bold text-(--nn-text)">
					Stories
				</h1>
				<p className="text-(--nn-text-dim)">Loading…</p>
			</div>
		);
	}

	return (
		<div className="mx-auto max-w-[1340px] space-y-6">
			{/* Intro */}
			<p className="font-mono text-[0.75rem] uppercase tracking-[0.12em] text-(--nn-text-dim)">
				Featured stories
			</p>
			<div className="flex items-center gap-3 mb-1.5">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-(--nn-text)">
					Stories
				</h1>
			</div>
			<p className="-mt-2 font-sans text-[0.85rem] leading-relaxed text-(--nn-text-dim)">
				Two stories the pipeline processed end-to-end where cross-source
				coverage was rich enough to make the consensus math meaningful — and
				where the two contrasting tempos, a slow arc and a fast surge, show
				what the instrument is actually measuring.
			</p>

			{/* Story cards */}
			<div className="grid gap-5 lg:grid-cols-2">
				{stories.map((story) => (
					<div
						key={story.id}
						className="flex flex-col rounded-[14px] border border-(--nn-border) bg-(--nn-surface) p-6"
					>
						{/* Title */}
						<h2 className="mb-1 font-heading text-[1.2rem] font-bold text-(--nn-text)">
							{story.title}
						</h2>

						{/* Tempo + coverage */}
						<div className="mb-4 space-y-0.5">
							<p className="font-mono text-[0.75rem] font-semibold text-(--nn-text)">
								{tempoLabel(story.spanDays)}
							</p>
							<p className="font-mono text-[0.75rem] text-(--nn-text-dim)">
								{fmtDate(story.coverageStart)} – {fmtDate(story.coverageEnd)}
							</p>
						</div>

						{/* Stat row */}
						<div className="mb-4 flex flex-wrap gap-x-5 gap-y-1 font-mono text-[0.75rem]">
							<span>
								<span className="font-semibold text-(--nn-text)">
									{story.articleCount}
								</span>
								<span className="text-(--nn-text-dim)"> articles</span>
							</span>
							<span>
								<span className="font-semibold text-(--nn-text)">
									{story.claimCount}
								</span>
								<span className="text-(--nn-text-dim)"> claims</span>
							</span>
							<span>
								<span className="font-semibold text-(--nn-text)">
									{story.sourceCount}
								</span>
								<span className="text-(--nn-text-dim)"> sources</span>
							</span>
							<span>
								<span className="font-semibold text-(--nn-text)">
									{story.absorbedCount}
								</span>
								<span className="text-(--nn-text-dim)"> absorbed</span>
							</span>
						</div>

						{/* Consensus statements */}
						{story.absorbedTexts.length > 0 && (
							<div className="mb-4">
								<h3 className="mb-2 font-heading text-[0.85rem] font-semibold text-(--nn-text)">
									What consensus formed on
								</h3>
								<div className="space-y-2">
									{story.absorbedTexts.map((text, i) => (
										<blockquote
											key={i}
											className="border-l-2 border-(--nn-navy) pl-3 font-sans text-[0.82rem] leading-relaxed italic text-(--nn-text-dim)"
										>
											{text}
										</blockquote>
									))}
								</div>
							</div>
						)}

						{/* Sources */}
						{story.sources.length > 0 && (
							<div className="mb-4">
								<h3 className="mb-1 font-heading text-[0.85rem] font-semibold text-(--nn-text)">
									Reported by
								</h3>
								<p className="font-sans text-[0.82rem] leading-relaxed text-(--nn-text-dim)">
									{story.sources.slice(0, 10).join(", ")}
									{story.sources.length > 10 ? "…" : ""}
								</p>
							</div>
						)}

						{/* Silent edits */}
						{story.silentEdits > 0 && (
							<div className="mb-4">
								<h3 className="mb-1 font-heading text-[0.85rem] font-semibold text-(--nn-text)">
									Silent edits detected
								</h3>
								<p className="font-mono text-[0.75rem] text-(--nn-text-dim)">
									{story.silentEdits} edit
									{story.silentEdits !== 1 ? "s" : ""} detected
								</p>
							</div>
						)}

						{/* Corrections */}
						{story.corrections > 0 && (
							<div className="mb-4">
								<h3 className="mb-1 font-heading text-[0.85rem] font-semibold text-(--nn-text)">
									Formal corrections
								</h3>
								<p className="font-mono text-[0.75rem] text-(--nn-text-dim)">
									{story.corrections} correction
									{story.corrections !== 1 ? "s" : ""} detected
								</p>
							</div>
						)}

						{/* Time to consensus */}
						{story.timeToConsensusMedian != null && (
							<div className="mb-4">
								<h3 className="mb-1 font-heading text-[0.85rem] font-semibold text-(--nn-text)">
									Time to consensus
								</h3>
								<p className="font-mono text-[0.75rem] text-(--nn-text-dim)">
									Median:{" "}
									<span className="font-semibold text-(--nn-text)">
										{story.timeToConsensusMedian}
									</span>{" "}
									day{story.timeToConsensusMedian !== 1 ? "s" : ""}
								</p>
								<p
									className="mt-0.5 font-sans text-[0.75rem] italic text-(--nn-text-dim)"
									title="Time between a claim's first appearance and its cross-source corroboration by ≥2 consensus-pool sources."
								>
									From first report to consensus-absorbed
								</p>
							</div>
						)}

						{/* CTA buttons */}
						<div className="mt-auto flex flex-wrap gap-2 pt-2">
							<Link
								to={`/cluster/${story.id}`}
								className="inline-flex items-center gap-1.5 rounded-lg border border-(--nn-navy) bg-(--nn-navy) px-4 py-2 font-heading text-[0.82rem] font-semibold text-white shadow-sm transition-all hover:brightness-110"
							>
								View Cluster Report
								<ArrowRight size={14} />
							</Link>
							{story.id === 966 && (
								<Link
									to={`/timeline/${story.id}`}
									className="inline-flex items-center gap-1.5 rounded-lg border border-(--nn-border) bg-(--nn-surface) px-4 py-2 font-heading text-[0.82rem] font-semibold text-(--nn-text) shadow-sm transition-all hover:border-(--nn-navy) hover:text-(--nn-navy)"
								>
									<Clock size={14} />
									View Timeline
								</Link>
							)}
						</div>
					</div>
				))}
			</div>
		</div>
	);
}
