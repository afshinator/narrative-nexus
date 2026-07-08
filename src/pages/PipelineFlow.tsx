import { Play, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";

// ── Types ────────────────────────────────────────────────────────────────

interface ScraperStatus {
	running: boolean;
	last_run: string | null;
	articles_inserted: number;
	readonly?: boolean;
}

interface ProviderInfo {
	id: string;
	name: string;
	model: string;
	amd: boolean;
}

interface ProviderCatalog {
	embeddings: ProviderInfo[];
	llm: ProviderInfo[];
}

interface ProviderAssignments {
	[key: string]: string;
}

// ── Provider badge colours ────────────────────────────────────────────────

const PROVIDER_BADGE: Record<string, { className: string; label: string }> = {
	fireworks: {
		className:
			"border-[var(--nn-red)] bg-[var(--nn-red-dim)] text-[var(--nn-red)]",
		label: "Fireworks API",
	},
	opencode: {
		className:
			"border-[var(--nn-teal)] bg-[var(--nn-teal-dim)] text-[var(--nn-teal)]",
		label: "OpenCode Zen",
	},
	deepseek: {
		className:
			"border-[var(--nn-navy)] bg-[var(--nn-navy-dim)] text-[var(--nn-navy)]",
		label: "DeepSeek API",
	},
	openai: {
		className:
			"border-[var(--nn-slate)] bg-[var(--nn-slate-dim)] text-[var(--nn-slate)]",
		label: "OpenAI",
	},
	"local-cpu": {
		className:
			"border-[var(--nn-slate)] bg-[var(--nn-slate-dim)] text-[var(--nn-slate)]",
		label: "Local CPU",
	},
};

// ── Default badge when provider ID is unknown ─────────────────────────────

function badgeFor(providerId: string): {
	className: string;
	label: string;
} {
	return (
		PROVIDER_BADGE[providerId] ?? {
			className:
				"border-[var(--nn-slate)] bg-[var(--nn-slate-dim)] text-[var(--nn-slate)]",
			label: providerId,
		}
	);
}

// ── Constants ─────────────────────────────────────────────────────────────

const DEBOUNCE_MS = 500;

export default function PipelineFlowPage() {
	const [status, setStatus] = useState<ScraperStatus | null>(null);
	const [error, setError] = useState("");
	const [pending, setPending] = useState(false);
	const errorTimer = useRef<ReturnType<typeof setTimeout> | undefined>(
		undefined,
	);

	// Provider state
	const [catalog, setCatalog] = useState<ProviderCatalog | null>(null);
	const [assignments, setAssignments] = useState<ProviderAssignments | null>(
		null,
	);

	const showError = (msg: string) => {
		clearTimeout(errorTimer.current);
		setError(msg);
		errorTimer.current = setTimeout(() => setError(""), 3000);
	};

	const fetchStatus = () => {
		fetch("/api/scraper/status")
			.then((r) =>
				r.ok ? r.json() : Promise.reject(new Error("bad response")),
			)
			.then(setStatus)
			.catch(() => setStatus(null));
	};

	const fetchProviders = () => {
		// Fetch catalog and assignments in parallel
		Promise.all([
			fetch("/api/config/providers/available").then((r) => r.json()),
			fetch("/api/config/providers").then((r) => r.json()),
		])
			.then(([cat, asgn]) => {
				setCatalog(cat.providers);
				setAssignments(asgn.providers);
			})
			.catch(() => {
				// Backend not running — leave null, UI shows offline state
			});
	};

	// biome-ignore lint/correctness/useExhaustiveDependencies: fetch on mount only
	useEffect(() => {
		fetchStatus();
		fetchProviders();
	}, []);

	const toggle = (action: "start" | "stop") => {
		setPending(true);
		setError("");
		clearTimeout(errorTimer.current);
		fetch(`/api/scraper/${action}`, { method: "POST" })
			.then(() => fetchStatus())
			.catch(() => showError(`${action} failed — retry?`))
			.finally(() => setTimeout(() => setPending(false), DEBOUNCE_MS));
	};

	// ── Provider helpers ───────────────────────────────────────────────

	const changeProvider = (slot: string, providerId: string) => {
		fetch("/api/config/providers", {
			method: "PUT",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ [slot]: providerId }),
		})
			.then((r) => (r.ok ? r.json() : Promise.reject(new Error("put failed"))))
			.then((data) => setAssignments(data.providers))
			.catch(() => showError("Failed to update provider"));
	};

	const hasProviders = catalog !== null && assignments !== null;

	return (
		<div className="mx-auto max-w-[780px] space-y-0">
			{/* Header */}
			<div
				className="animate-fade-up"
				style={{ "--i": 0 } as React.CSSProperties}
			>
				<div className="flex items-center justify-between gap-4">
					<div>
						<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
							Pipeline Flow
						</h1>
						<p className="font-sans text-[0.88rem] text-[var(--nn-text-dim)]">
							The 4-agent swarm architecture &mdash; configurable per-stage
							providers
						</p>
					</div>
				</div>
			</div>

			{/* F1+F5: Legend — compute-class summary instead of per-slot pills */}
			<div
				className="animate-fade-up mb-8 mt-7 rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] px-[22px] py-4"
				style={{ "--i": 1 } as React.CSSProperties}
			>
				{hasProviders ? (
					(() => {
						const slots = Object.entries(assignments as Record<string, string>)
							// P1: exclude claim_matching — internal pipeline, not an agent stage
							.filter(([slot]) => slot !== "claim_matching_embedding");
						// Count distinct providers + always-CPU for consensus
						const counts = new Map<string, number>();
						for (const [, pid] of slots) {
							const b = badgeFor(pid);
							const key = b.label.includes("CPU") ? "CPU" : pid;
							counts.set(key, (counts.get(key) ?? 0) + 1);
						}
						// F5b: all-AI-on-Fireworks status line
						const aiSlots = slots.filter(([s]) => s !== "consensus");
						const allAmd = aiSlots.length > 0 && aiSlots.every(([, pid]) => badgeFor(pid).label.includes("Fireworks"));
						return (
							<>
								{allAmd && (
									<p className="mb-3 font-heading text-[0.82rem] font-semibold text-[var(--nn-red)]">
										All AI stages running on AMD Instinct accelerators via Fireworks AI
									</p>
								)}
								<div className="flex flex-wrap gap-4">
									{[...counts.entries()].map(([pid, count]) => {
										const b = badgeFor(pid);
										return (
											<LegendItem
												key={pid}
												badge={
													<span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 font-mono text-[0.75rem] font-medium uppercase tracking-[0.03em] ${b.className}`}>
														{b.label}
													</span>
												}
												label={`${count} stage${count > 1 ? "s" : ""}`}
											/>
										);
									})}
								</div>
							</>
						);
					})()
				) : (
					<>
						<LegendItem
							badge={
								<span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--nn-red)] bg-[var(--nn-red-dim)] px-3 py-1 font-mono text-[0.75rem] font-medium uppercase tracking-[0.03em] text-[var(--nn-red)]">
									AMD GPU
								</span>
							}
							label="Embeddings"
						/>
						<LegendItem
							badge={
								<span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--nn-navy)] bg-[var(--nn-navy-dim)] px-3 py-1 font-mono text-[0.75rem] font-medium uppercase tracking-[0.03em] text-[var(--nn-navy)]">
									API
								</span>
							}
							label="LLM Inference"
						/>
						<LegendItem
							badge={
								<span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--nn-slate)] bg-[var(--nn-slate-dim)] px-3 py-1 font-mono text-[0.75rem] font-medium uppercase tracking-[0.03em] text-[var(--nn-slate)]">
									CPU
								</span>
							}
							label="Consensus Math · Snapshots"
						/>
					</>
				)}
			</div>

			{/* Scraper Controls */}
			<div
				className="animate-fade-up rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5"
				style={{ "--i": 1.5 } as React.CSSProperties}
			>
				<div className="flex items-center gap-4">
					<button
						type="button"
						disabled={pending || status === null || status?.readonly}
						onClick={() => toggle(status?.running ? "stop" : "start")}
						className={`inline-flex items-center gap-2 rounded-lg border px-6 py-2.5 font-heading text-[0.84rem] font-semibold shadow-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:brightness-110 ${
							status?.readonly
								? "border-[var(--nn-border)] bg-[var(--nn-surface)] text-[var(--nn-text-dim)]"
								: status?.running
								? "border-[var(--nn-red)] bg-[var(--nn-red)] text-white"
								: "border-[var(--nn-teal)] bg-[var(--nn-teal)] text-white"
						}`}
					>
						{status?.readonly ? (
							<>Scraper (paused)</>
						) : status?.running ? (
							<>
								<Square size={14} fill="currentColor" /> Stop
							</>
						) : (
							<>
								<Play size={14} fill="currentColor" /> Start
							</>
						)}
					</button>
					<span className="font-mono text-[0.75rem] tabular-nums text-[var(--nn-text-dim)]">
						{status
							? status.running
								? `Running · ${status.articles_inserted} articles · last run ${status.last_run?.slice(11, 16) ?? "—"}`
								: "Paused"
							: "No connection — start backend to control scraper"}
					</span>
				</div>
				{error && (
					<p className="mt-3 font-sans text-[0.75rem] text-[var(--nn-red)]">
						{error}
					</p>
				)}
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
						desc="Generates sentence-transformer embeddings and clusters stories by semantic similarity. Groups related coverage across sources into coherent story clusters."
						index={1}
					>
						<Accordion
							badge={badgeFor(assignments?.agent1_embedding ?? "local-cpu")}
							title="Embeddings"
							body="Sentence transformers run locally on CPU (384-dim). DBSCAN clusters articles by cosine-similarity. Provider configurable via dropdown — switch to Fireworks or OpenAI when API keys are set."
							dropdown={
								hasProviders
									? {
											value: assignments?.agent1_embedding,
											options: catalog?.embeddings,
											onChange: (id) => changeProvider("agent1_embedding", id),
										}
									: undefined
							}
						/>
						<Accordion
							badge={badgeFor(assignments?.agent1_llm ?? "opencode")}
							title="Classification"
							body="LLM classifies story vertical and resolves entity disambiguation. Runs on the configured LLM provider — OpenCode Zen (free tier) by default, switchable to Fireworks for AMD Instinct inference."
							dropdown={
								hasProviders
									? {
											value: assignments?.agent1_llm,
											options: catalog?.llm,
											onChange: (id) => changeProvider("agent1_llm", id),
										}
									: undefined
							}
						/>
					</StageCard>

					<Connector c={1} i={1} />

					{/* Stage 2 */}
					<StageCard
						num="2"
						name="Forensic Extraction"
						desc="Strips editorial framing and extracts atomic factual claims from each article. Every claim is a verifiable statement in structured JSON."
						index={2}
					>
						<Accordion
							badge={badgeFor(assignments?.agent2_llm ?? "opencode")}
							title="Claim Extraction"
							body="LLM performs framing neutralization then extracts atomic claims as structured JSON. Each claim includes article text and entity references. Provider configurable — defaults to OpenCode Zen, switchable to any configured LLM provider."
							dropdown={
								hasProviders
									? {
											value: assignments?.agent2_llm,
											options: catalog?.llm,
											onChange: (id) => changeProvider("agent2_llm", id),
										}
									: undefined
							}
						/>
					</StageCard>

					<Connector c={2} i={2} />

					{/* Stage 3 */}
					<StageCard
						num="3"
						name="Consensus Alignment"
						desc="Computes cross-source agreement over the Tier 1+2 consensus pool. Classifies claims into the lifecycle state machine and assigns convergence type."
						index={3}
					>
						<Accordion
							badge={{
								className:
									"border-[var(--nn-slate)] bg-[var(--nn-slate-dim)] text-[var(--nn-slate)]",
								label: "CPU",
							}}
							title="Consensus Math"
							body="Pure Python — no GPU required. Computes source agreement graphs, applies configurable threshold (65–90%), classifies claims, assigns convergence type, and updates all six reputation dimensions per source per vertical per day."
						/>
					</StageCard>

					<Connector c={3} i={3} />

					{/* Stage 4 */}
					<StageCard
						num="4"
						name="Silent Auditor"
						desc="Compares historical article snapshots to detect unreported edits. When a source changes an article without issuing a formal correction, the Silent Auditor flags it."
						index={4}
					>
						<Accordion
							badge={badgeFor(assignments?.agent4_llm ?? "opencode")}
							title="Diff Engine"
							body="Re-fetches article bodies and diffs against stored snapshots using text comparison. Flags changes above 10% threshold. Provider configurable for the LLM-based significance evaluation (future). Currently runs on CPU for text diffing."
							dropdown={
								hasProviders
									? {
											value: assignments?.agent4_llm,
											options: catalog?.llm,
											onChange: (id) => changeProvider("agent4_llm", id),
										}
									: undefined
							}
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
					<strong className="text-[var(--nn-text)]">
						{hasProviders ? "Pipeline ready" : "Pipeline offline"}
					</strong>{" "}
					&mdash;{" "}
					{hasProviders
						? "Backend connected. Provider assignments loaded."
						: "No backend connected. All four agents will activate when the agent swarm runs against live article feeds."}
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
		<div className="flex items-center gap-2 font-sans text-[0.75rem] text-[var(--nn-text-dim)]">
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
			<div className="font-sans text-[0.75rem] text-[var(--nn-text-dim)]">
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
			<div
				className="animate-connector-flow absolute left-1/2 top-0 bottom-0 w-[2px] -translate-x-1/2 bg-[var(--nn-slate)]"
				style={
					{ animationDelay: `calc(var(--c, 0) * 350ms)` } as React.CSSProperties
				}
			/>
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
	dropdown,
}: {
	badge: { className: string; label: string };
	title: string;
	body: string;
	dropdown?: {
		value: string;
		options: ProviderInfo[];
		onChange: (id: string) => void;
	};
}) {
	return (
		<details className="group flex-1 min-w-[160px] overflow-hidden rounded-[10px] border border-[var(--nn-border)] bg-[var(--nn-surface2)] transition-colors duration-200 open:border-[var(--nn-navy)]">
			<summary className="flex cursor-pointer select-none items-center gap-2 px-4 py-3.5 font-heading text-[0.78rem] font-semibold text-[var(--nn-text)] transition-colors duration-200 hover:text-[var(--nn-navy)] list-none [&::-webkit-details-marker]:hidden">
				<span
					className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono text-[0.75rem] font-medium uppercase tracking-[0.03em] ${badge.className}`}
				>
					{badge.label}
				</span>
				{title}
				{/* Provider dropdown */}
				{dropdown && (
					<select
						value={dropdown.value}
						onChange={(e) => dropdown.onChange(e.target.value)}
						onClick={(e) => e.stopPropagation()}
						className="ml-2 rounded-md border border-[var(--nn-border)] bg-[var(--nn-surface)] px-2 py-0.5 font-mono text-[0.75rem] text-[var(--nn-text)] outline-none focus:border-[var(--nn-navy)] cursor-pointer"
					>
						{dropdown.options.map((p) => (
							<option key={p.id} value={p.id}>
								{p.name}{p.amd ? " (AMD)" : ""} — {p.model}
							</option>
						))}
					</select>
				)}
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
					<p className="font-sans text-[0.75rem] leading-[1.45] text-[var(--nn-text-dim)] m-0">
						{body}
					</p>
				</div>
			</div>
		</details>
	);
}
