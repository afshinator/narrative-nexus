import type { Archetype } from "../store";
import { useStore } from "../store";

const PILLS: { label: string; value: Archetype | null }[] = [
	{ label: "All sources", value: null },
	{ label: "Early Breaker", value: "EARLY_BREAKER" },
	{ label: "Unmatched Breaker", value: "NOISE_GENERATOR" },
	{ label: "Late but Reliable", value: "SELECTIVE_ACCURATE" },
	{ label: "Consensus Echo", value: "CONSENSUS_FOLLOWER" },
];

const TOKEN: Record<string, string> = {
	EARLY_BREAKER: "var(--nn-navy)",
	NOISE_GENERATOR: "var(--nn-red)",
	SELECTIVE_ACCURATE: "var(--nn-teal)",
	CONSENSUS_FOLLOWER: "var(--nn-slate)",
};

export default function ArchetypePills() {
	const filter = useStore((s) => s.archetypeFilter);
	const setFilter = useStore((s) => s.setArchetypeFilter);

	return (
		<div className="flex flex-wrap gap-2">
			{PILLS.map((pill) => {
				const active = filter === pill.value;
				return (
					<button
						key={pill.label}
						type="button"
						onClick={() => setFilter(pill.value)}
						className={`rounded-full border px-3.5 py-1.5 text-[0.84rem] font-medium transition-colors ${
							active
								? "text-[var(--nn-navy)] border-[var(--nn-navy)]"
								: "border-[var(--nn-border)] text-[var(--nn-text-dim)] hover:border-[var(--nn-text-dim)] hover:text-[var(--nn-text)]"
						}`}
						style={
							active && pill.value
								? {
										backgroundColor: `color-mix(in srgb, ${TOKEN[pill.value]} 10%, transparent)`,
										borderColor: TOKEN[pill.value],
										color: TOKEN[pill.value],
									}
								: undefined
						}
					>
						{pill.label}
					</button>
				);
			})}
		</div>
	);
}
