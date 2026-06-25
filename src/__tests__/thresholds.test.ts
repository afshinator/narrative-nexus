import { describe, expect, it } from "vitest";

// Pure data — no imports needed, just structure tests
describe("DEFAULT_THRESHOLDS", () => {
	it("is an object with three vertical keys", async () => {
		const { DEFAULT_THRESHOLDS } = await import("../data/thresholds");
		expect(DEFAULT_THRESHOLDS).toHaveProperty("geopolitics");
		expect(DEFAULT_THRESHOLDS).toHaveProperty("economics");
		expect(DEFAULT_THRESHOLDS).toHaveProperty("technology");
	});

	it("has correct default values", async () => {
		const { DEFAULT_THRESHOLDS } = await import("../data/thresholds");
		expect(DEFAULT_THRESHOLDS.geopolitics).toBe(65);
		expect(DEFAULT_THRESHOLDS.economics).toBe(75);
		expect(DEFAULT_THRESHOLDS.technology).toBe(75);
	});

	it("all values are numbers in range 0-100", async () => {
		const { DEFAULT_THRESHOLDS } = await import("../data/thresholds");
		for (const value of Object.values(DEFAULT_THRESHOLDS)) {
			expect(value).toBeTypeOf("number");
			expect(value).toBeGreaterThan(0);
			expect(value).toBeLessThanOrEqual(100);
		}
	});
});

describe("Thresholds type", () => {
	it("has exactly three keys", async () => {
		const { DEFAULT_THRESHOLDS } = await import("../data/thresholds");
		expect(Object.keys(DEFAULT_THRESHOLDS)).toHaveLength(3);
	});
});
