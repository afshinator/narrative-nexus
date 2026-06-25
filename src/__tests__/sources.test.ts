import { describe, expect, it } from "vitest";

describe("DEFAULT_SOURCES", () => {
	it("has exactly 20 entries", async () => {
		const { DEFAULT_SOURCES } = await import("../data/sources");
		expect(DEFAULT_SOURCES).toHaveLength(20);
	});

	it("has 5 distinct tiers", async () => {
		const { DEFAULT_SOURCES } = await import("../data/sources");
		const tiers = new Set(DEFAULT_SOURCES.map((s) => s.tier));
		expect(tiers.size).toBe(5);
		expect(tiers.has(1)).toBe(true);
		expect(tiers.has(5)).toBe(true);
	});

	it("Tier 1 has exactly 5 sources (consensus pool)", async () => {
		const { DEFAULT_SOURCES } = await import("../data/sources");
		const tier1 = DEFAULT_SOURCES.filter((s) => s.tier === 1);
		expect(tier1).toHaveLength(5);
	});

	it("Tier 2 has exactly 5 sources (consensus pool)", async () => {
		const { DEFAULT_SOURCES } = await import("../data/sources");
		const tier2 = DEFAULT_SOURCES.filter((s) => s.tier === 2);
		expect(tier2).toHaveLength(5);
	});

	it("each source has id, name, domain, tier", async () => {
		const { DEFAULT_SOURCES } = await import("../data/sources");
		for (const source of DEFAULT_SOURCES) {
			expect(source).toHaveProperty("id");
			expect(source).toHaveProperty("name");
			expect(source).toHaveProperty("domain");
			expect(source).toHaveProperty("tier");
			expect(typeof source.id).toBe("string");
			expect(typeof source.name).toBe("string");
			expect(typeof source.domain).toBe("string");
			expect(typeof source.tier).toBe("number");
		}
	});
});

describe("Pure helper: getSourcesByTier", () => {
	it("groups sources by tier", async () => {
		const { getSourcesByTier } = await import("../data/sources");
		const groups = getSourcesByTier();
		expect(groups).toHaveProperty("1");
		expect(groups).toHaveProperty("5");
		expect(groups["1"]).toHaveLength(5);
	});
});
