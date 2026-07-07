// Shared reputation score types.
// Imported by SourcesPage and SourceProfilePage.

/** Reputation score for one source in one vertical at a point in time. */
export interface ReputationScore {
	sourceId: string;
	vertical: string;
	R_orig: number; // 0–100 trait (no favorable direction)
	R_val: number; // 0–100 graded (high = favorable)
	R_speed: number; // 0–100 graded (low = favorable — inverted on radar)
	R_frame: number; // 0–100 graded (low = favorable — inverted on radar)
	R_edit: number; // 0–100 graded (low = favorable — inverted on radar)
	R_correct: number; // 0–100 trait (no favorable direction)
}

/** Daily reputation snapshot — one row per source × vertical × day. */
export interface DailySnapshot {
	sourceId: string;
	vertical: string;
	day: number; // sequential index from 0
	date: string; // ISO date string e.g. "2026-03-03"
	R_orig: number; // 0–100 percentile
	R_val: number;
	R_speed: number;
	R_frame: number;
	R_edit: number;
	R_correct: number;
}

/** Timeline event marker on the day scrubber. */
export interface ProfileEvent {
	day: number;
	type: "CLAIM_ABSORBED" | "SILENT_EDIT" | "CLAIM_UNRESOLVED";
	title: string;
	detail: string;
}

/** Dimension definitions for radar axes, stat panel, and sparklines. */
export interface DimensionDef {
	key: keyof Omit<DailySnapshot, "sourceId" | "vertical" | "day">;
	label: string;
	trait: boolean; // true = neutral color, no polarity
}

export const DIMENSIONS: DimensionDef[] = [
	{ key: "R_orig", label: "Origination", trait: true },
	{ key: "R_val", label: "Validation", trait: false },
	{ key: "R_speed", label: "Speed Premium", trait: false },
	{ key: "R_frame", label: "Framing Consist.", trait: false },
	{ key: "R_edit", label: "Silent Edits", trait: false },
	{ key: "R_correct", label: "Corrections", trait: true },
];
