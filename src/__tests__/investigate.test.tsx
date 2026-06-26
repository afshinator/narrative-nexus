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

	it("stores query result on submit", async () => {
		const { user } = renderPage();
		const textarea = screen.getByRole("textbox");
		await user.type(textarea, "https://example.com/article");
		await user.click(screen.getByRole("button", { name: /submit/i }));

		const { useStore } = await import("../store");
		const results = useStore.getState().adHocResults;
		expect(results).toHaveLength(1);
		expect(results[0].query).toBe("https://example.com/article");
	});

	it("shows submitted query in results list", async () => {
		const { user } = renderPage();
		const textarea = screen.getByRole("textbox");
		await user.type(textarea, "https://example.com/article");
		await user.click(screen.getByRole("button", { name: /submit/i }));

		expect(screen.getByText("https://example.com/article")).toBeInTheDocument();
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
