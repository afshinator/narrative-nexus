import { useState } from "react";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { useStore } from "../store";

const TERMS = [
	{
		term: "Consensus Reality",
		definition:
			'The version of events agreed upon by the majority of the panel at a given threshold. Not "the truth."',
	},
	{
		term: "Consensus-Absorbed",
		definition:
			"A claim that has entered the consensus version of events. Terminal state.",
	},
	{
		term: "Cross-Source Convergent",
		definition:
			"A consensus-absorbed claim that was independently corroborated by another source before absorption.",
	},
	{
		term: "Self-Consistent",
		definition:
			"A consensus-absorbed claim where only the origin source published consistent follow-up; no independent corroboration, but the panel eventually agreed.",
	},
	{
		term: "Unresolved",
		definition:
			"A claim that never became consensus-absorbed after 90 days. Terminal state.",
	},
	{
		term: "Outlier Claim",
		definition:
			"A claim present in one or few sources but absent from the consensus baseline at extraction time.",
	},
] as const;

interface Props {
	open: boolean;
	onOpenChange: (open: boolean) => void;
}

export function OnboardingDialog({ open, onOpenChange }: Props) {
	const [dontShow, setDontShow] = useState(false);
	const setOnboardingComplete = useStore((s) => s.setOnboardingComplete);

	function handleOpenChange(next: boolean) {
		if (!next) {
			setDontShow(false);
			if (dontShow) setOnboardingComplete(true);
		}
		onOpenChange(next);
	}

	return (
		<Dialog open={open} onOpenChange={handleOpenChange}>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle>Glossary</DialogTitle>
					<DialogDescription>
						Narrative Nexus tracks consensus reality, not truth.
					</DialogDescription>
				</DialogHeader>

				<div className="space-y-4 max-h-[60vh] overflow-y-auto">
					{TERMS.map(({ term, definition }) => (
						<div key={term}>
							<h3 className="text-sm font-semibold text-foreground">{term}</h3>
							<p className="text-sm text-muted-foreground">{definition}</p>
						</div>
					))}
				</div>

				<div className="flex items-center justify-between pt-2">
					<label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
						<input
							type="checkbox"
							checked={dontShow}
							onChange={(e) => setDontShow(e.target.checked)}
							className="size-3.5 rounded border-border"
						/>
						Don&apos;t show on startup
					</label>
				</div>
			</DialogContent>
		</Dialog>
	);
}
