export default function PipelineFlowPage() {
	return (
		<div className="mx-auto max-w-[780px] space-y-0">
			{/* Header */}
			<div
				className="animate-fade-up"
				style={{ "--i": 0 } as React.CSSProperties}
			>
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					Pipeline Flow
				</h1>
				<p className="font-sans text-[0.88rem] text-[var(--nn-text-dim)]">
					The 4-agent swarm architecture &mdash; what runs where, and why
				</p>
			</div>

			{/* Legend */}
			<div
				className="animate-fade-up mb-8 mt-7 flex flex-wrap gap-4 rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] px-[22px] py-4"
				style={{ "--i": 1 } as React.CSSProperties}
			>
				<LegendItem
					badge={
						<span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--nn-red)] bg-[var(--nn-red-dim)] px-3 py-1 font-mono text-[0.66rem] font-medium uppercase tracking-[0.03em] text-[var(--nn-red)]">
							AMD GPU
						</span>
					}
					label="ROCm · Embeddings"
				/>
				<LegendItem
					badge={
						<span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--nn-navy)] bg-[var(--nn-navy-dim)] px-3 py-1 font-mono text-[0.66rem] font-medium uppercase tracking-[0.03em] text-[var(--nn-navy)]">
							Fireworks API
						</span>
					}
					label="LLM Inference on AMD Instinct"
				/>
				<LegendItem
					badge={
						<span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--nn-slate)] bg-[var(--nn-slate-dim)] px-3 py-1 font-mono text-[0.66rem] font-medium uppercase tracking-[0.03em] text-[var(--nn-slate)]">
							CPU
						</span>
					}
					label="Consensus Math · Snapshots"
				/>
			</div>

			{/* Pipeline */}
			<div
				className="animate-fade-up"
				style={{ "--i": 2 } as React.CSSProperties}
			>
				<div className="flex flex-col items-stretch">
					{/* Entry: RSS */}
					<EndpointCard
						icon="📡"
						label="Article Ingest"
						desc="RSS polling via feedparser · CPU"
						index={0}
					/>

					<Connector c={0} i={0} />

					{/* Stage 1 */}
					<StageCard
						num="1"
						name="Intake & Clustering"
						desc="Ingests articles, generates sentence-transformer embeddings, and clusters stories by semantic similarity. Groups related coverage across sources into coherent story clusters for downstream analysis."
						index={1}
					>
						<Accordion
							badge={{
								text: "AMD GPU",
								className:
									"border-[var(--nn-red)] bg-[var(--nn-red-dim)] text-[var(--nn-red)]",
							}}
							title="Embeddings"
							body="Sentence transformers run on ROCm via the worker container. BERTopic clusters articles by semantic similarity. VRAM-light (<2GB), fits any Radeon pod."
						/>
						<Accordion
							badge={{
								text: "Fireworks API",
								className:
									"border-[var(--nn-navy)] bg-[var(--nn-navy-dim)] text-[var(--nn-navy)]",
							}}
							title="Classification"
							body="LLM classifies story vertical (geopolitics / economics / technology) and resolves entity disambiguation. Runs on AMD Instinct MI325X/MI355X via Fireworks."
						/>
					</StageCard>

					<Connector c={1} i={1} />

					{/* Stage 2 */}
					<StageCard
						num="2"
						name="Forensic Extraction"
						desc="Strips editorial framing and extracts atomic factual claims from each article. Every claim is a verifiable statement in structured JSON — not a summary, not a paraphrase, not a sentiment score."
						index={2}
					>
						<Accordion
							badge={{
								text: "Fireworks API",
								className:
									"border-[var(--nn-navy)] bg-[var(--nn-navy-dim)] text-[var(--nn-navy)]",
							}}
							title="Claim Extraction"
							body="LLM performs framing neutralization (strips adjectives, hedges, passive-voice attribution) then extracts atomic claims as structured JSON. Each claim includes source article, extracted text, and entity references. Model: Llama 3.3 70B or DeepSeek-V4-Pro (benchmarked at access time)."
						/>
					</StageCard>

					<Connector c={2} i={2} />

					{/* Stage 3 */}
					<StageCard
						num="3"
						name="Consensus Alignment"
						desc="Computes cross-source agreement over the Tier 1+2 consensus pool. Classifies claims into the lifecycle state machine and assigns convergence type. Drives the reputation dimensions that power every chart on this dashboard."
						index={3}
					>
						<Accordion
							badge={{
								text: "CPU",
								className:
									"border-[var(--nn-slate)] bg-[var(--nn-slate-dim)] text-[var(--nn-slate)]",
							}}
							title="Consensus Math"
							body="Pure Python — no GPU required. Computes source agreement graphs, applies configurable threshold (65–90%), classifies claims as Consensus-Absorbed or Unresolved, assigns convergence type (Cross-Source Convergent / Self-Consistent), and updates all six reputation dimensions per source per vertical per day. Runs on the app server alongside the API."
						/>
					</StageCard>

					<Connector c={3} i={3} />

					{/* Stage 4 */}
					<StageCard
						num="4"
						name="Silent Auditor"
						desc="Compares historical article snapshots to detect unreported edits. When a source changes an article without issuing a formal correction, the Silent Auditor logs the diff and flags it in the source's reputation profile."
						index={4}
					>
						<Accordion
							badge={{
								text: "CPU",
								className:
									"border-[var(--nn-slate)] bg-[var(--nn-slate-dim)] text-[var(--nn-slate)]",
							}}
							title="Diff Engine"
							body="Re-fetches article bodies on a schedule and diffs against stored snapshots. Detects: text changes, paragraph reordering, headline rewrites, and byline changes. Flags changes not accompanied by a formal correction notice. Runs on the app server; no GPU needed for text diffing."
						/>
					</StageCard>

					<Connector c={4} i={4} />

					{/* Exit: DB */}
					<EndpointCard
						icon="🗄️"
						label="Database"
						desc="SQLite WAL · Sources, articles, clusters, claims, snapshots"
						index={5}
					/>
				</div>
			</div>

			{/* Status */}
			<div
				className="animate-fade-up mt-8 flex items-center gap-3 rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] px-6 py-[18px]"
				style={{ "--i": 3 } as React.CSSProperties}
			>
				<div className="h-2.5 w-2.5 shrink-0 rounded-full bg-[var(--nn-slate)] animate-status-breathe" />
				<p className="font-sans text-[0.82rem] text-[var(--nn-text-dim)]">
					<strong className="text-[var(--nn-text)]">Pipeline offline</strong>{" "}
					&mdash; no backend connected. All four agents will activate when the
					agent swarm runs against live article feeds. This diagram shows the
					static architecture; live status and replay mode will be available
					when the pipeline produces data.
				</p>
			</div>
		</div>
	);
}

/* ── Sub-components ── */

function LegendItem({
	badge,
	label,
}: {
	badge: React.ReactNode;
	label: string;
}) {
	return (
		<div className="flex items-center gap-2 font-sans text-[0.74rem] text-[var(--nn-text-dim)]">
			{badge}
			<span>{label}</span>
		</div>
	);
}

function EndpointCard({
	icon,
	label,
	desc,
	index,
}: {
	icon: string;
	label: string;
	desc: string;
	index: number;
}) {
	return (
		<div
			className="animate-fade-up-card rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface2)] px-6 py-5 text-center transition-colors duration-200 hover:border-[var(--nn-teal)]"
			style={
				{
					"--i": index,
					animationDelay: `calc(var(--i, 0) * 100ms + 350ms)`,
				} as React.CSSProperties
			}
		>
			<div className="mb-1 text-[1.3rem] text-[var(--nn-text-dim)]">{icon}</div>
			<div className="font-heading text-[0.9rem] font-semibold text-[var(--nn-text)]">
				{label}
			</div>
			<div className="font-sans text-[0.72rem] text-[var(--nn-text-dim)]">
				{desc}
			</div>
		</div>
	);
}

function Connector({ c, i }: { c: number; i: number }) {
	return (
		<div
			className="animate-fade-up-card relative flex h-10 items-center justify-center"
			style={
				{
					"--i": i,
					"--c": c,
					animationDelay: `calc(var(--i, 0) * 100ms + 500ms)`,
				} as React.CSSProperties
			}
		>
			{/* stem */}
			<div
				className="animate-connector-flow absolute left-1/2 top-0 bottom-0 w-[2px] -translate-x-1/2 bg-[var(--nn-slate)]"
				style={
					{ animationDelay: `calc(var(--c, 0) * 350ms)` } as React.CSSProperties
				}
			/>
			{/* chevron arrow */}
			<div
				className="animate-connector-flow relative z-10 rounded bg-[var(--nn-bg)] px-1.5 py-0.5"
				style={
					{ animationDelay: `calc(var(--c, 0) * 350ms)` } as React.CSSProperties
				}
			>
				<svg
					viewBox="0 0 14 10"
					className="block h-[10px] w-[14px]"
					aria-hidden="true"
				>
					<path
						d="M2 2 L7 7 L12 2"
						fill="none"
						stroke="var(--nn-slate)"
						strokeWidth="2"
						strokeLinecap="round"
						strokeLinejoin="round"
					/>
				</svg>
			</div>
		</div>
	);
}

function StageCard({
	num,
	name,
	desc,
	children,
	index,
}: {
	num: string;
	name: string;
	desc: string;
	children: React.ReactNode;
	index: number;
}) {
	return (
		<div
			className="animate-fade-up-card rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6 transition-all duration-200 hover:translate-x-1 hover:border-[var(--nn-navy)] hover:shadow-[4px_0_20px_rgba(0,0,0,0.2)]"
			style={
				{
					"--i": index,
					animationDelay: `calc(var(--i, 0) * 100ms + 350ms)`,
				} as React.CSSProperties
			}
		>
			{/* Stage header */}
			<div className="mb-2.5 flex items-center gap-3">
				<span className="font-heading text-[1.5rem] font-bold leading-none text-[var(--nn-navy)]">
					{num}
				</span>
				<h2 className="flex-1 font-heading text-[1.05rem] font-semibold text-[var(--nn-text)]">
					{name}
				</h2>
				<div className="h-2.5 w-2.5 shrink-0 rounded-full bg-[var(--nn-slate)] animate-status-breathe" />
			</div>
			<p className="mb-4 font-sans text-[0.82rem] leading-[1.55] text-[var(--nn-text-dim)]">
				{desc}
			</p>
			<div className="flex flex-wrap gap-3">{children}</div>
		</div>
	);
}

function Accordion({
	badge,
	title,
	body,
}: {
	badge: { text: string; className: string };
	title: string;
	body: string;
}) {
	return (
		<details className="group flex-1 min-w-[160px] overflow-hidden rounded-[10px] border border-[var(--nn-border)] bg-[var(--nn-surface2)] transition-colors duration-200 open:border-[var(--nn-navy)]">
			<summary className="flex cursor-pointer select-none items-center gap-2 px-4 py-3.5 font-heading text-[0.78rem] font-semibold text-[var(--nn-text)] transition-colors duration-200 hover:text-[var(--nn-navy)] list-none [&::-webkit-details-marker]:hidden">
				<span
					className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono text-[0.62rem] font-medium uppercase tracking-[0.03em] ${badge.className}`}
				>
					{badge.text}
				</span>
				{title}
				<svg
					viewBox="0 0 12 12"
					className="ml-auto h-3 w-3 transition-transform duration-[250ms] group-open:rotate-180"
					aria-hidden="true"
				>
					<path
						d="M3 5 L6 8 L9 5"
						fill="none"
						stroke="var(--nn-text-dim)"
						strokeWidth="1.5"
						strokeLinecap="round"
						strokeLinejoin="round"
					/>
				</svg>
			</summary>
			<div className="grid grid-rows-[0fr] transition-[grid-template-rows] duration-300 group-open:grid-rows-[1fr]">
				<div className="overflow-hidden px-4 pb-3.5">
					<p className="font-sans text-[0.72rem] leading-[1.45] text-[var(--nn-text-dim)] m-0">
						{body}
					</p>
				</div>
			</div>
		</details>
	);
}
