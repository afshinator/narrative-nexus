import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";
import InvestigatePage from "../pages/Investigate";

function renderPage() {
	const user = userEvent.setup();
	return {
		user,
		...render(
			<MemoryRouter>
				<InvestigatePage />
			</MemoryRouter>,
		),
	};
}

describe("Investigate Page", () => {
	beforeEach(async () => {
		const { useStore } = await import("../store");
		useStore.setState({ adHocResults: [] });
	});

	it("renders page heading", () => {
		renderPage();
		expect(
			screen.getByRole("heading", { name: /investigate/i }),
		).toBeInTheDocument();
	});

	it("renders snapshot banner with exact text", () => {
		renderPage();
		expect(
			screen.getByText(
				/claim resolution states are not available for ad-hoc reports/i,
			),
		).toBeInTheDocument();
	});

	it("renders a textarea for query input", () => {
		renderPage();
		expect(screen.getByRole("textbox")).toBeInTheDocument();
	});

	it("renders a submit button", () => {
		renderPage();
		expect(screen.getByRole("button", { name: /submit/i })).toBeInTheDocument();
	});

	it("shows empty state when no results", () => {
		renderPage();
		expect(screen.getByText(/no ad-hoc queries yet/i)).toBeInTheDocument();
	});

	it("does NOT store empty result on submit — shows transient status instead", async () => {
		const { user } = renderPage();
		const textarea = screen.getByRole("textbox");
		await user.type(textarea, "https://example.com/article");
		await user.click(screen.getByRole("button", { name: /submit/i }));

		// Should show transient submitted message
		expect(screen.getByText(/submitted/i)).toBeInTheDocument();

		// Should NOT add to the store
		const { useStore } = await import("../store");
		expect(useStore.getState().adHocResults).toHaveLength(0);
	});

	it("removes individual result via per-card dismiss button", async () => {
		const { useStore } = await import("../store");
		useStore.setState({
			adHocResults: [{ id: "a", query: "first", timestamp: 1, claims: [] }],
		});
		const { user } = renderPage();
		expect(screen.getByText("first")).toBeInTheDocument();
		await user.click(screen.getByRole("button", { name: /dismiss result/i }));
		expect(useStore.getState().adHocResults).toHaveLength(0);
	});

	it("clear results button empties the list", async () => {
		const { useStore } = await import("../store");
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
		const { user } = renderPage();
		await user.click(screen.getByRole("button", { name: /clear results/i }));
		expect(useStore.getState().adHocResults).toEqual([]);
	});
});
