// Single source of truth for consensus threshold defaults.
// Modify values here to change defaults app-wide.
// Per REQ-024: GEOPOLITICS 65%, ECONOMICS 75%, TECHNOLOGY 75%.

export type VerticalThresholdKey = "geopolitics" | "economics" | "technology";

export type Thresholds = Record<VerticalThresholdKey, number>;

export const DEFAULT_THRESHOLDS: Thresholds = {
	geopolitics: 65,
	economics: 75,
	technology: 75,
};

export const VERTICAL_LABELS: Record<VerticalThresholdKey, string> = {
	geopolitics: "Geopolitics",
	economics: "Economics",
	technology: "Technology",
};

export const VERTICAL_ORDER: VerticalThresholdKey[] = [
	"geopolitics",
	"economics",
	"technology",
];
