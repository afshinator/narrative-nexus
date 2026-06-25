import type { Archetype } from "../store";

export function getArchetype(
	rOrig: number,
	rVal: number,
	medianOrig: number,
	medianVal: number,
): Archetype {
	if (rOrig > medianOrig && rVal > medianVal) return "EARLY_BREAKER";
	if (rOrig > medianOrig && rVal <= medianVal) return "NOISE_GENERATOR";
	if (rOrig <= medianOrig && rVal > medianVal) return "SELECTIVE_ACCURATE";
	return "CONSENSUS_FOLLOWER";
}
