// Trait dimensions never get a color — they're always neutral
const TRAIT_DIMENSIONS = new Set(["R_orig", "R_correct"]);

export function getPolarityColor(
	dimension: string,
	percentile: number,
): string {
	if (TRAIT_DIMENSIONS.has(dimension)) return "var(--nn-slate)";
	if (percentile >= 66) return "var(--nn-teal)";
	if (percentile >= 33) return "var(--nn-amber)";
	return "var(--nn-red)";
}
