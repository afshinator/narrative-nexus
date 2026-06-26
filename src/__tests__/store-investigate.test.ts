import { describe, expect, it } from "vitest";
import { useStore } from "../store";

describe("adHocResults store", () => {
	it("defaults to empty array", () => {
		useStore.setState({ adHocResults: [] });
		expect(useStore.getState().adHocResults).toEqual([]);
	});

	it("addAdHocResult appends a result", () => {
		useStore.setState({ adHocResults: [] });
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
});
