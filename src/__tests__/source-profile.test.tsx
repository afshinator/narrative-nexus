import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SourceProfilePage from "../pages/SourceProfile";

// Chart.js needs Canvas — jsdom doesn't have it
vi.mock("react-chartjs-2", () => ({
	Radar: () => <canvas data-testid="radar-chart" aria-label="radar chart" />,
}));

function renderPage(route = "/source/reuters.com") {
	return render(
		<MemoryRouter initialEntries={[route]}>
			<Routes>
				<Route path="/source/:domain" element={<SourceProfilePage />} />
			</Routes>
		</MemoryRouter>,
	);
}

describe("SourceProfile Page", () => {
	beforeEach(async () => {
		const { useStore } = await import("../store");
		useStore.setState({ activeSources: [] });
	});

	it("renders source name and metadata from route param", () => {
		renderPage();
		expect(
			screen.getByRole("heading", { name: /reuters/i }),
		).toBeInTheDocument();
		expect(screen.getByText(/reuters\.com/i)).toBeInTheDocument();
	});

	it("shows source not found for unknown domain", () => {
		renderPage("/source/nonexistent.invalid");
		expect(screen.getByText(/not found/i)).toBeInTheDocument();
		expect(
			screen.getByRole("link", { name: /back to sources/i }),
		).toBeInTheDocument();
	});

	it("renders 3 vertical picker pills", () => {
		renderPage();
		expect(
			screen.getByRole("button", { name: /geopolitics/i }),
		).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: /economics/i }),
		).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: /technology/i }),
		).toBeInTheDocument();
	});

	it("changes active vertical on pill click", async () => {
		const user = userEvent.setup();
		renderPage();
		const econ = screen.getByRole("button", { name: /economics/i });
		await user.click(econ);
		expect(econ.className).toContain("border");
	});

	// UX15-B: Two-tier stat panel — hero row (Origination/Validation) + secondary (Speed/Framing)
	it("renders stat panel with two-tier layout", () => {
		renderPage();
		// Hero row: Origination and Validation as the two scatter-plot axes
		expect(screen.getAllByText(/origination/i).length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText(/validation/i).length).toBeGreaterThanOrEqual(1);
		// Secondary row: Speed and Framing
		expect(screen.getAllByText(/speed/i).length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText(/framing/i).length).toBeGreaterThanOrEqual(1);
		// Dead dims collapsed into one line — no separate "Silent Edits" or "Corrections" rows
		expect(screen.queryByText("Silent Edits")).toBeNull();
		expect(screen.queryByText("Corrections")).toBeNull();
		// No per-row "no events detected" — dead dims collapsed
		expect(screen.queryByText("no events detected")).toBeNull();
		// No meaning clauses ("reports claims before others", "steadiness of editorial tone")
		expect(screen.queryByText(/reports claims before/i)).toBeNull();
		expect(screen.queryByText(/steadiness of editorial/i)).toBeNull();
		// No Δ annotations
		expect(screen.queryByText(/Δ/)).toBeNull();
	});

	it("stat panel shows '—' for uncomputed values in empty state", () => {
		renderPage();
		const dashes = screen.getAllByText("—");
		expect(dashes.length).toBeGreaterThanOrEqual(4);
	});

	it('renders archetype badge with "Unclassified" in empty state', () => {
		renderPage();
		expect(screen.getByText(/unclassified/i)).toBeInTheDocument();
	});

	it("renders radar empty state when dimensions are null", () => {
		renderPage();
		expect(
			screen.getByText(/hasn.*t crossed the.*2-source corroboration/i),
		).toBeInTheDocument();
	});

	// UX14: SparklineGrid + VfTrendChart unmounted
	it("no longer renders sparkline grid or validation-over-time", () => {
		renderPage();
		expect(screen.queryByText("30-Day Trends")).toBeNull();
		expect(screen.queryByText("Validation over time")).toBeNull();
	});

	it("vertical pills default to GEOPOLITICS active", () => {
		renderPage();
		const geopolitics = screen.getByRole("button", { name: /geopolitics/i });
		expect(geopolitics.className).toContain("font-heading");
	});
});
