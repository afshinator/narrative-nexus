import { describe, expect, it } from "vitest";
import { useStore } from "../store";

describe("adHocResults store", () => {
	beforeEach(() => {
		useStore.setState({ adHocResults: [] });
	});

	it("defaults to empty array", () => {
		expect(useStore.getState().adHocResults).toEqual([]);
	});

	it("addAdHocResult appends a result", () => {
		const result = {
			id: "test-1",
			query: "https://example.com/article",
			timestamp: 1234567890,
			claims: [],
		};
		useStore.getState().addAdHocResult(result);
		expect(useStore.getState().adHocResults).toHaveLength(1);
		expect(useStore.getState().adHocResults[0].query).toBe(
			"https://example.com/article",
		);
	});

	it("clearAdHocResults empties the array", () => {
		useStore.setState({
			adHocResults: [
				{
					id: "test-1",
					query: "test",
					timestamp: 1,
					claims: [],
				},
			],
		});
		useStore.getState().clearAdHocResults();
		expect(useStore.getState().adHocResults).toEqual([]);
	});

	it("removeAdHocResult removes a single result by id", () => {
		useStore.setState({
			adHocResults: [
				{ id: "a", query: "first", timestamp: 1, claims: [] },
				{ id: "b", query: "second", timestamp: 2, claims: [] },
				{ id: "c", query: "third", timestamp: 3, claims: [] },
			],
		});
		useStore.getState().removeAdHocResult("b");
		const remaining = useStore.getState().adHocResults;
		expect(remaining).toHaveLength(2);
		expect(remaining[0].id).toBe("a");
		expect(remaining[1].id).toBe("c");
	});

	it("removeAdHocResult is a no-op for unknown id", () => {
		useStore.setState({
			adHocResults: [{ id: "a", query: "first", timestamp: 1, claims: [] }],
		});
		useStore.getState().removeAdHocResult("nonexistent");
		expect(useStore.getState().adHocResults).toHaveLength(1);
	});
});
