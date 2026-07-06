import { beforeEach, describe, expect, it } from "vitest";

describe("Store — consensusThresholds", () => {
	beforeEach(async () => {
		const { useStore } = await import("../store");
		useStore.setState({
			consensusThresholds: {
				geopolitics: 65,
				economics: 75,
				technology: 75,
			},
		});
	});

	it("initializes from DEFAULT_THRESHOLDS", async () => {
		const { useStore } = await import("../store");
		const { DEFAULT_THRESHOLDS } = await import("../data/thresholds");
		const state = useStore.getState();
		expect(state.consensusThresholds).toEqual(DEFAULT_THRESHOLDS);
	});

	it("setConsensusThreshold updates one vertical", async () => {
		const { useStore } = await import("../store");
		useStore.getState().setConsensusThreshold("geopolitics", 70);
		expect(useStore.getState().consensusThresholds.geopolitics).toBe(70);
		expect(useStore.getState().consensusThresholds.economics).toBe(75);
	});

	it("resetThresholds restores defaults", async () => {
		const { useStore } = await import("../store");
		const { DEFAULT_THRESHOLDS } = await import("../data/thresholds");
		useStore.getState().setConsensusThreshold("geopolitics", 99);
		useStore.getState().resetThresholds();
		expect(useStore.getState().consensusThresholds).toEqual(DEFAULT_THRESHOLDS);
	});
});

describe("Store — activeSources", () => {
	it("initializes with all source IDs active", async () => {
		const { useStore } = await import("../store");
		const { DEFAULT_SOURCES } = await import("../data/sources");
		// Reset to ensure we test the actual initial state
		useStore.setState({ activeSources: DEFAULT_SOURCES.map((s) => s.id) });
		const state = useStore.getState();
		const allIds = DEFAULT_SOURCES.map((s) => s.id);
		expect(state.activeSources).toEqual(allIds);
	});

	it("toggleSource removes an active source", async () => {
		const { useStore } = await import("../store");
		const { DEFAULT_SOURCES } = await import("../data/sources");
		// Start with all active
		useStore.setState({ activeSources: DEFAULT_SOURCES.map((s) => s.id) });
		const firstId = DEFAULT_SOURCES[0].id;
		useStore.getState().toggleSource(firstId);
		expect(useStore.getState().activeSources).not.toContain(firstId);
		// Other sources still active
		expect(useStore.getState().activeSources).toContain(DEFAULT_SOURCES[1].id);
	});

	it("toggleSource re-adds an inactive source", async () => {
		const { useStore } = await import("../store");
		const { DEFAULT_SOURCES } = await import("../data/sources");
		const firstId = DEFAULT_SOURCES[0].id;
		// Start with first source inactive
		useStore.setState({
			activeSources: DEFAULT_SOURCES.slice(1).map((s) => s.id),
		});
		useStore.getState().toggleSource(firstId);
		expect(useStore.getState().activeSources).toContain(firstId);
	});
});
