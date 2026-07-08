import { Play, RotateCcw, Square } from "lucide-react";
import { startTransition, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { VERTICAL_LABELS, VERTICAL_ORDER } from "../data/thresholds";
import { useStore } from "../store";
import { formatPercent } from "../utils/format";

const FONT_PRESETS = [
	{ value: "1.0", label: "Default" },
	{ value: "1.1", label: "Large" },
	{ value: "1.2", label: "Larger" },
] as const;

const THRESHOLD_PRESETS = [50, 60, 65, 75, 85, 90] as const;

interface ScraperStatus {
	running: boolean;
	last_run: string | null;
	articles_inserted: number;
	readonly?: boolean;
}

export default function SettingsPage() {
	const theme = useStore((s) => s.theme);
	const setTheme = useStore((s) => s.setTheme);
	const thresholds = useStore((s) => s.consensusThresholds);
	const setConsensusThreshold = useStore((s) => s.setConsensusThreshold);
	const resetThresholds = useStore((s) => s.resetThresholds);
	const fontScale = useStore((s) => s.fontScale);
	const setFontScale = useStore((s) => s.setFontScale);

	// Scraper state
	const [scraperStatus, setScraperStatus] = useState<ScraperStatus | null>(null);
	const [scraperPending, setScraperPending] = useState(false);
	const [scraperError, setScraperError] = useState("");

	const fetchScraper = () => {
		fetch("/api/scraper/status")
			.then((r) => (r.ok ? r.json() : Promise.reject(new Error("bad response"))))
			.then(setScraperStatus)
			.catch(() => setScraperStatus(null));
	};

	// biome-ignore lint/correctness/useExhaustiveDependencies: fetch on mount only
	useEffect(() => {
		fetchScraper();
	}, []);

	const toggleScraper = (action: "start" | "stop") => {
		setScraperPending(true);
		setScraperError("");
		fetch(`/api/scraper/${action}`, { method: "POST" })
			.then(() => fetchScraper())
			.catch(() => setScraperError(`${action} failed — retry?`))
			.finally(() => setTimeout(() => setScraperPending(false), 500));
	};

	return (
		<div className="mx-auto max-w-2xl space-y-6">
			{/* Page header — mock style */}
			<div className="flex items-center gap-3 mb-1.5">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					Settings
				</h1>
			</div>
			<p className="-mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
				Configure thresholds, appearance, and preferences
			</p>

			{/* Scraper Control — relocated from Pipeline (UX30) */}
			<Card className="p-6">
				<h2 className="mb-4 text-base font-medium text-foreground">
					Scraper
				</h2>
				<p className="mb-3 font-sans text-[0.82rem] leading-relaxed text-[var(--nn-text-dim)]">
					Runs continuously in production: polls RSS feeds, ingests, and
					rescans on a schedule. Paused against the demo corpus by default.
				</p>
				<div className="flex items-center gap-4">
					<button
						type="button"
						disabled={scraperPending || scraperStatus === null || scraperStatus?.readonly}
						onClick={() => toggleScraper(scraperStatus?.running ? "stop" : "start")}
						className={`inline-flex items-center gap-2 rounded-lg border px-6 py-2.5 font-heading text-[0.84rem] font-semibold shadow-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:brightness-110 ${
							scraperStatus?.readonly
								? "border-[var(--nn-border)] bg-[var(--nn-surface)] text-[var(--nn-text-dim)]"
								: scraperStatus?.running
									? "border-[var(--nn-red)] bg-[var(--nn-red)] text-white"
									: "border-[var(--nn-teal)] bg-[var(--nn-teal)] text-white"
						}`}
					>
						{scraperStatus?.readonly ? (
							<>Scraper (paused)</>
						) : scraperStatus?.running ? (
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
						{scraperStatus
							? scraperStatus.running
								? `Running · ${scraperStatus.articles_inserted} articles · last run ${scraperStatus.last_run?.slice(11, 16) ?? "—"}`
								: "Paused"
							: "No connection — start backend to control scraper"}
					</span>
				</div>
				{scraperError && (
					<p className="mt-3 font-sans text-[0.75rem] text-[var(--nn-red)]">
						{scraperError}
					</p>
				)}
			</Card>

			{/* Font Scale */}
			<Card className="p-6">
				<h2 className="mb-4 text-base font-medium text-foreground">
					Font Scale
				</h2>
				<div className="flex flex-wrap gap-1">
					{FONT_PRESETS.map((p) => (
						<button
							key={p.value}
							type="button"
							onClick={() => setFontScale(Number.parseFloat(p.value))}
							className={`rounded-md border px-2.5 py-1 font-mono text-xs tabular-nums transition-colors ${
								fontScale === Number.parseFloat(p.value)
									? "border-[var(--nn-navy)] bg-[var(--nn-navy)] text-white"
									: "border-[var(--nn-border)] text-muted-foreground hover:border-[var(--nn-text-dim)] hover:text-foreground"
							}`}
						>
							{p.label}
						</button>
					))}
				</div>
			</Card>

			{/* Theme */}
			<Card className="p-6">
				<h2 className="mb-4 text-base font-medium text-foreground">Theme</h2>
				<div className="flex items-center justify-between">
					<span className="text-sm text-muted-foreground">Dark mode</span>
					<Switch
						checked={theme === "dark"}
						onCheckedChange={(v) => startTransition(() => setTheme(v ? "dark" : "light"))}
						aria-label="Toggle dark mode"
					/>
				</div>
			</Card>

			{/* Consensus Thresholds — kept at bottom intentionally */}
			<Card className="p-6">
				<div className="mb-4 flex items-center justify-between">
					<h2 className="text-base font-medium text-foreground">
						Consensus Thresholds
					</h2>
					<Button
						variant="ghost"
						size="sm"
						onClick={resetThresholds}
						aria-label="Reset thresholds to defaults"
					>
						<RotateCcw size={14} />
						Reset
					</Button>
				</div>
				<div className="space-y-5">
					{VERTICAL_ORDER.map((key) => (
						<div key={key} className="space-y-2">
							<div className="flex items-center justify-between">
								<span className="text-sm text-muted-foreground">
									{VERTICAL_LABELS[key]}
								</span>
								<span className="font-mono text-sm tabular-nums text-foreground">
									{formatPercent(thresholds[key])}
								</span>
							</div>
							<div className="flex flex-wrap gap-1">
								{THRESHOLD_PRESETS.map((preset) => (
									<button
										key={preset}
										type="button"
										onClick={() => setConsensusThreshold(key, preset)}
										className={`rounded-md border px-2.5 py-1 font-mono text-xs tabular-nums transition-colors ${
											thresholds[key] === preset
												? "border-[var(--nn-navy)] bg-[var(--nn-navy)] text-white"
												: "border-[var(--nn-border)] text-muted-foreground hover:border-[var(--nn-text-dim)] hover:text-foreground"
										}`}
									>
										{preset}%
									</button>
								))}
							</div>
						</div>
					))}
				</div>
				<p className="mt-4 text-xs leading-relaxed text-[var(--nn-text-dim)]">
					These thresholds determine how many sources must report a claim before
					it enters the consensus baseline. Adjusting them changes claim
					classification across all stories. Based on{" "}
					<a
						href="https://en.wikipedia.org/wiki/Consensus_decision-making"
						target="_blank"
						rel="noopener noreferrer"
						className="underline underline-offset-2 hover:text-foreground"
					>
						consensus methodology research
					</a>{" "}
					— 75% is the most commonly employed threshold across academic and
					intelligence domains.
				</p>
			</Card>
		</div>
	);
}
