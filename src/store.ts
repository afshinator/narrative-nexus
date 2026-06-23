import { create } from "zustand"
import { persist } from "zustand/middleware"

// Use string literal unions — NOT enums (banned by erasableSyntaxOnly in TS6)
export type Theme = "dark" | "light"
export type Vertical = "ALL" | "GEOPOLITICS" | "ECONOMICS" | "TECHNOLOGY"
export type Archetype =
  | "EARLY_BREAKER"
  | "NOISE_GENERATOR"
  | "SELECTIVE_ACCURATE"
  | "CONSENSUS_FOLLOWER"
  | null

interface StoreState {
  theme: Theme
  vertical: Vertical
  archetypeFilter: Archetype
  fontScale: number
  onboardingComplete: boolean
  setTheme: (theme: Theme) => void
  setVertical: (vertical: Vertical) => void
  setArchetypeFilter: (f: Archetype) => void
  setFontScale: (scale: number) => void
  setOnboardingComplete: (v: boolean) => void
}

export const useStore = create<StoreState>()(
  persist(
    (set) => ({
      theme: "dark",
      vertical: "ALL",
      archetypeFilter: null,
      fontScale: 1.0,
      onboardingComplete: false,
      setTheme: (theme) => set({ theme }),
      setVertical: (vertical) => set({ vertical }),
      setArchetypeFilter: (archetypeFilter) => set({ archetypeFilter }),
      setFontScale: (fontScale) => set({ fontScale }),
      setOnboardingComplete: (onboardingComplete) => set({ onboardingComplete }),
    }),
    { name: "nn-store" }
  )
)