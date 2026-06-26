import { Search, Send, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useStore } from "../store";

const STATUS_TIMEOUT = 3000;

export default function InvestigatePage() {
	const [query, setQuery] = useState("");
	const [submitted, setSubmitted] = useState(false);
	const timeoutRef = useRef<ReturnType<typeof setTimeout>>(null);
	const adHocResults = useStore((s) => s.adHocResults);
	const removeAdHocResult = useStore((s) => s.removeAdHocResult);
	const clearAdHocResults = useStore((s) => s.clearAdHocResults);

	useEffect(() => {
		return () => {
			if (timeoutRef.current) clearTimeout(timeoutRef.current);
		};
	}, []);

	function handleSubmit() {
		const trimmed = query.trim();
		if (!trimmed) return;
		setSubmitted(true);
		setQuery("");
		if (timeoutRef.current) clearTimeout(timeoutRef.current);
		timeoutRef.current = setTimeout(() => setSubmitted(false), STATUS_TIMEOUT);
	}

	return (
		<div className="mx-auto max-w-[780px] space-y-6">
			{/* Header */}
			<div>
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					Investigate
				</h1>
				<p className="-mt-1 font-sans text-[0.88rem] text-[var(--nn-text-dim)]">
					Ad-hoc forensic query tool
				</p>
			</div>

			{/* Snapshot banner */}
			<div className="rounded-[14px] border border-[var(--nn-amber)] bg-[var(--nn-amber)]/10 px-5 py-4">
				<p className="font-sans text-[0.82rem] leading-relaxed text-[var(--nn-amber)]">
					Claim resolution states are not available for ad-hoc reports. This
					analysis runs pipeline stages 1&ndash;3 in read-only mode.
				</p>
			</div>

			{/* Query form */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6">
				<h2 className="mb-4 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
					Query
				</h2>
				<textarea
					value={query}
					onChange={(e) => setQuery(e.target.value)}
					placeholder="Paste an article URL or full text..."
					rows={5}
					className="mb-4 w-full resize-y rounded-[10px] border border-[var(--nn-border)] bg-[var(--nn-surface2)] px-4 py-3 font-sans text-[0.84rem] text-[var(--nn-text)] placeholder:text-[var(--nn-text-dim)] focus:border-[var(--nn-navy)] focus:outline-none"
				/>
				<div className="flex items-center gap-4">
					<button
						type="button"
						onClick={handleSubmit}
						disabled={!query.trim()}
						className="inline-flex items-center gap-2 rounded-full border border-[var(--nn-navy)] bg-[var(--nn-navy)] px-5 py-2 font-heading text-[0.82rem] font-semibold text-white transition-opacity disabled:opacity-40"
					>
						<Send size={14} />
						Submit
					</button>
					{submitted && (
						<span className="font-sans text-[0.82rem] text-[var(--nn-teal)]">
							Submitted &mdash; pipeline analysis will populate results when the
							backend runs stages 1&ndash;3.
						</span>
					)}
				</div>
			</div>

			{/* Results */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6">
				<div className="mb-4 flex items-center justify-between">
					<h2 className="font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
						Results
					</h2>
					{adHocResults.length > 0 && (
						<button
							type="button"
							onClick={clearAdHocResults}
							className="font-mono text-[0.72rem] text-[var(--nn-text-dim)] hover:text-[var(--nn-text)] transition-colors"
						>
							Clear Results
						</button>
					)}
				</div>

				{adHocResults.length === 0 ? (
					<div className="py-8 text-center">
						<Search
							size={28}
							className="mx-auto mb-3 text-[var(--nn-text-dim)]"
						/>
						<p className="font-sans text-[0.82rem] text-[var(--nn-text-dim)]">
							No ad-hoc queries yet. Submit an article URL or paste text to run
							a forensic analysis through pipeline stages 1&ndash;3.
						</p>
					</div>
				) : (
					<div className="space-y-3">
						{[...adHocResults].reverse().map((result) => (
							<div
								key={result.id}
								className="rounded-[10px] border border-[var(--nn-border)] bg-[var(--nn-surface2)] p-4"
							>
								<div className="mb-3 flex items-start justify-between gap-4">
									<div className="min-w-0 flex-1">
										<p className="truncate font-mono text-[0.78rem] text-[var(--nn-text)]">
											{result.query}
										</p>
										<p className="mt-1 font-sans text-[0.7rem] text-[var(--nn-text-dim)]">
											{new Date(result.timestamp).toLocaleString()}
										</p>
									</div>
									<button
										type="button"
										onClick={() => removeAdHocResult(result.id)}
										className="shrink-0 rounded p-1 text-[var(--nn-text-dim)] hover:text-[var(--nn-text)] transition-colors"
										aria-label="Dismiss result"
									>
										<X size={14} />
									</button>
								</div>
								{result.claims.length === 0 ? (
									<p className="font-sans text-[0.74rem] italic text-[var(--nn-text-dim)]">
										No claims extracted yet. Pipeline analysis will populate
										results when the backend runs stages 1&ndash;3.
									</p>
								) : (
									<div className="space-y-2">
										{result.claims.map((claim, i) => (
											<div
												key={claim.text || i}
												className="rounded-md border border-[var(--nn-border)] bg-[var(--nn-surface)] px-3 py-2"
											>
												<p className="font-sans text-[0.78rem] text-[var(--nn-text)]">
													{claim.text}
												</p>
												<div className="mt-1.5 flex flex-wrap gap-3 font-mono text-[0.68rem] text-[var(--nn-text-dim)]">
													<span>
														{claim.sources.length} source
														{claim.sources.length !== 1 ? "s" : ""}
													</span>
													{claim.consensusPct != null && (
														<span>{claim.consensusPct}% consensus</span>
													)}
												</div>
											</div>
										))}
									</div>
								)}
							</div>
						))}
					</div>
				)}
			</div>
		</div>
	);
}
