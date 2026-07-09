import { Play, RotateCcw, Square } from "lucide-react";
import { startTransition, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
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
	disabled?: boolean;
}

type ConfirmAction = "start" | "stop" | null;

export default function SettingsPage() {
	const theme = useStore((s) => s.theme);
	const setTheme = useStore((s) => s.setTheme);
	const thresholds = useStore((s) => s.consensusThresholds);
	const setConsensusThreshold = useStore((s) => s.setConsensusThreshold);
	const resetThresholds = useStore((s) => s.resetThresholds);
	const fontScale = useStore((s) => s.fontScale);
	const setFontScale = useStore((s) => s.setFontScale);

	const [scraperStatus, setScraperStatus] = useState<ScraperStatus | null>(null);
	const [scraperPending, setScraperPending] = useState(false);
	const [scraperError, setScraperError] = useState("");
	const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);

	const fetchScraper = () => {
		fetch("/api/scraper/status")
			.then((r) => (r.ok ? r.json() : Promise.reject(new Error("bad response"))))
			.then(setScraperStatus)
			.catch(() => setScraperStatus(null));
	};

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

	const handleConfirm = () => {
		if (!confirmAction) return;
		toggleScraper(confirmAction);
		setConfirmAction(null);
	};

	const isRunning = scraperStatus?.running === true;
	const isScraperDisabled = scraperStatus?.disabled === true;

	return (
		<div className="mx-auto max-w-2xl space-y-6">
			<div className="flex items-center gap-3 mb-1.5">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					Settings
				</h1>
			</div>
			<p className="-mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
				Configure thresholds, appearance, and preferences
			</p>

			{/* Scraper Control */}
			<Card className="p-6">
				<h2 className="mb-4 text-base font-medium text-foreground">
					Scraper
				</h2>
				{isScraperDisabled ? (
					<p className="mb-3 font-sans text-[0.82rem] leading-relaxed text-[var(--nn-amber)] font-medium">
						Scraper disabled on this deployment.
					</p>
				) : (
					<p className="mb-3 font-sans text-[0.82rem] leading-relaxed text-[var(--nn-text-dim)]">
						{isRunning
							? "Polling RSS feeds from 37 sources, ingesting new articles, and rescanning on a schedule."
							: "Polls RSS feeds from 37 sources, ingests new articles, and rescans on a schedule. Paused by default — press Start to begin live collection."}
					</p>
				)}
				<div className="flex items-center gap-4">
					<button
						type="button"
						disabled={scraperPending || scraperStatus === null || isScraperDisabled}
						onClick={() => setConfirmAction(isRunning ? "stop" : "start")}
						className={`inline-flex items-center gap-2 rounded-lg border px-6 py-2.5 font-heading text-[0.84rem] font-semibold shadow-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:brightness-110 ${
							isRunning
								? "border-[var(--nn-red)] bg-[var(--nn-red)] text-white"
								: "border-[var(--nn-teal)] bg-[var(--nn-teal)] text-white"
						}`}
					>
						{isRunning ? (
							<>
								<Square size={14} fill="currentColor" /> Stop Scraper
							</>
						) : (
							<>
								<Play size={14} fill="currentColor" /> Start Scraper
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

			{/* Confirmation modals */}
			<Dialog open={confirmAction !== null} onOpenChange={() => setConfirmAction(null)}>
				<DialogContent className="max-w-md">
					<DialogHeader>
						<DialogTitle>
							{confirmAction === "start" ? "Start live collection?" : "Stop live collection?"}
						</DialogTitle>
						<DialogDescription className="pt-2 font-sans text-[0.82rem] leading-relaxed text-[var(--nn-text-dim)]">
							{confirmAction === "start"
								? "The scraper will begin polling RSS feeds from the 37 sources and ingesting new articles into this instance's database. New clusters, claims, and reputation snapshots will accumulate."
								: "Scraping will pause. Existing data remains — no articles or claims are removed. You can restart at any time."}
						</DialogDescription>
					</DialogHeader>
					<div className="mt-4 flex justify-end gap-3">
						<button
							type="button"
							onClick={() => setConfirmAction(null)}
							className="rounded-lg border border-[var(--nn-border)] px-4 py-2 font-heading text-[0.84rem] font-semibold text-[var(--nn-text-dim)] hover:bg-[var(--nn-surface2)] transition-colors"
						>
							Cancel
						</button>
						<button
							type="button"
							onClick={handleConfirm}
							className={`rounded-lg border px-4 py-2 font-heading text-[0.84rem] font-semibold text-white shadow-sm transition-all hover:brightness-110 ${
								confirmAction === "stop"
									? "border-[var(--nn-red)] bg-[var(--nn-red)]"
									: "border-[var(--nn-teal)] bg-[var(--nn-teal)]"
							}`}
						>
							{confirmAction === "start" ? "Start" : "Stop"}
						</button>
					</div>
				</DialogContent>
			</Dialog>

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

			{/* Consensus Thresholds */}
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
