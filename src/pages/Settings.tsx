import { RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import type { VerticalThresholdKey } from "../data/thresholds";
import { useStore } from "../store";
import { formatPercent } from "../utils/format";

const VERTICAL_LABELS: Record<VerticalThresholdKey, string> = {
	geopolitics: "Geopolitics",
	economics: "Economics",
	technology: "Technology",
};

const VERTICAL_ORDER: VerticalThresholdKey[] = [
	"geopolitics",
	"economics",
	"technology",
];

const FONT_PRESETS = [
	{ value: "0.8", label: "80%" },
	{ value: "0.9", label: "90%" },
	{ value: "1.0", label: "100%" },
	{ value: "1.1", label: "110%" },
	{ value: "1.2", label: "120%" },
] as const;

const THRESHOLD_PRESETS = [50, 60, 65, 75, 85, 90] as const;

export default function SettingsPage() {
	const theme = useStore((s) => s.theme);
	const setTheme = useStore((s) => s.setTheme);
	const thresholds = useStore((s) => s.consensusThresholds);
	const setConsensusThreshold = useStore((s) => s.setConsensusThreshold);
	const resetThresholds = useStore((s) => s.resetThresholds);
	const fontScale = useStore((s) => s.fontScale);
	const setFontScale = useStore((s) => s.setFontScale);

	return (
		<div className="mx-auto max-w-2xl space-y-6">
			{/* Page header — mock style */}
			<div className="pagehead">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					Settings
				</h1>
			</div>
			<p className="-mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
				Configure thresholds, appearance, and preferences
			</p>

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
						onCheckedChange={(v) => setTheme(v ? "dark" : "light")}
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
