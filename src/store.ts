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

interface StoreState {
	theme: Theme;
	archetypeFilter: Archetype;
	fontScale: number;
	onboardingComplete: boolean;
	consensusThresholds: Thresholds;
	activeSources: string[];
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
		}),
		{ name: "nn-store" },
	),
);
