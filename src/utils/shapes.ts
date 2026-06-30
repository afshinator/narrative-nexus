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

// D3 symbol types for scatter plot markers
export const TIER_D3_SYMBOL: Record<number, SymbolType> = {
	1: symbolCircle,
	2: symbolSquare,
	3: symbolDiamond,
	4: symbolTriangle,
	5: symbolCross,
};
