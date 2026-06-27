/** Source outlet format → scatter plot marker shape.
 *  Modify mappings here to change scatter plot visual encoding. */

import type { SymbolType } from "d3";
import {
	symbolCircle,
	symbolCross,
	symbolDiamond,
	symbolSquare,
	symbolTriangle,
} from "d3";

// Shape names correspond to D3 symbol types: circle, square, diamond, triangle, cross
export const TIER_SHAPE: Record<number, string> = {
	1: "circle", // Wire / Consensus anchor
	2: "square", // Mainstream editorial
	3: "diamond", // International
	4: "triangle", // Independent / Investigative
	5: "cross", // Contrarian
} as const;

export function getShapeForTier(tier: number): string {
	return TIER_SHAPE[tier] ?? "circle";
}

// D3 symbol types for scatter plot markers (review-03 M07 — dedup from ScatterPlot)
export const TIER_D3_SYMBOL: Record<number, SymbolType> = {
	1: symbolCircle,
	2: symbolSquare,
	3: symbolDiamond,
	4: symbolTriangle,
	5: symbolCross,
};
