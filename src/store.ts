import { create } from "zustand";
import { persist } from "zustand/middleware";
import { DEFAULT_SOURCES } from "./data/sources";
import type { Thresholds, VerticalThresholdKey } from "./data/thresholds";
import { DEFAULT_THRESHOLDS } from "./data/thresholds";

// Use string literal unions — NOT enums (banned by erasableSyntaxOnly in TS6)
export type Theme = "dark" | "light";
export type Archetype =
	| "EARLY_BREAKER"
	| "NOISE_GENERATOR"
	| "SELECTIVE_ACCURATE"
	| "CONSENSUS_FOLLOWER"
	| null;

export interface AdHocClaim {
	text: string;
	sources: string[];
	consensusPct: number | null;
}

export interface AdHocResult {
	id: string;
	query: string;
	timestamp: number;
	claims: AdHocClaim[];
}

interface StoreState {
	theme: Theme;
	archetypeFilter: Archetype;
	fontScale: number;
	onboardingComplete: boolean;
	consensusThresholds: Thresholds;
	activeSources: string[];
	adHocResults: AdHocResult[];
	setTheme: (theme: Theme) => void;
	setArchetypeFilter: (f: Archetype) => void;
	setFontScale: (scale: number) => void;
	setOnboardingComplete: (v: boolean) => void;
	setConsensusThreshold: (
		vertical: VerticalThresholdKey,
		value: number,
	) => void;
	resetThresholds: () => void;
	toggleSource: (id: string) => void;
	addAdHocResult: (result: AdHocResult) => void;
	clearAdHocResults: () => void;
	removeAdHocResult: (id: string) => void;
}

export const useStore = create<StoreState>()(
	persist(
		(set) => ({
			theme: "dark",
			archetypeFilter: null,
			fontScale: 1.0,
			onboardingComplete: false,
			consensusThresholds: DEFAULT_THRESHOLDS,
			activeSources: DEFAULT_SOURCES.map((s) => s.id),
			adHocResults: [],
			setTheme: (theme) => set({ theme }),
			setArchetypeFilter: (archetypeFilter) => set({ archetypeFilter }),
			setFontScale: (fontScale) => set({ fontScale }),
			setOnboardingComplete: (onboardingComplete) =>
				set({ onboardingComplete }),
			setConsensusThreshold: (vertical, value) =>
				set((state) => ({
					consensusThresholds: {
						...state.consensusThresholds,
						[vertical]: value,
					},
				})),
			resetThresholds: () => set({ consensusThresholds: DEFAULT_THRESHOLDS }),
			toggleSource: (id) =>
				set((state) => ({
					activeSources: state.activeSources.includes(id)
						? state.activeSources.filter((s) => s !== id)
						: [...state.activeSources, id],
				})),
			addAdHocResult: (result) =>
				set((state) => ({
					adHocResults: [...state.adHocResults, result],
				})),
			clearAdHocResults: () => set({ adHocResults: [] }),
			removeAdHocResult: (id) =>
				set((state) => ({
					adHocResults: state.adHocResults.filter((r) => r.id !== id),
				})),
		}),
		{ name: "nn-store" },
	),
);
