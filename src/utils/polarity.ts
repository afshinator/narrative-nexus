// Trait dimensions never get a color — they're always neutral
const TRAIT_DIMENSIONS = new Set(["R_orig", "R_correct"]);

// Dimensions where low values are favorable (review-03 H01)
export const INVERTED_DIMS = new Set(["R_speed", "R_frame", "R_edit"]);

export function getPolarityColor(
	dimension: string,
	percentile: number,
): string {
	if (TRAIT_DIMENSIONS.has(dimension)) return "var(--nn-slate)";
	const effective = INVERTED_DIMS.has(dimension)
		? 100 - percentile
		: percentile;
	if (effective >= 66) return "var(--nn-teal)";
	if (effective >= 33) return "var(--nn-amber)";
	return "var(--nn-red)";
}
