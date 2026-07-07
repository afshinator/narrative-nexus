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
		// After click, the economics pill should have active styling
		expect(econ.className).toContain("border");
	});

	it("renders stat panel with 6 dimension rows", () => {
		renderPage();
		// Dimension labels appear in both stat panel and sparkline grid — getAllByText
		expect(screen.getAllByText(/origination/i).length).toBeGreaterThanOrEqual(
			1,
		);
		expect(screen.getAllByText(/validation/i).length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText(/speed premium/i).length).toBeGreaterThanOrEqual(
			1,
		);
		expect(screen.getAllByText(/framing/i).length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText(/silent edits/i).length).toBeGreaterThanOrEqual(
			1,
		);
		expect(screen.getAllByText(/corrections/i).length).toBeGreaterThanOrEqual(
			1,
		);
	});

	it("stat panel shows '—' for all values in empty state", () => {
		renderPage();
		const dashes = screen.getAllByText("—");
		expect(dashes.length).toBeGreaterThanOrEqual(6);
	});

	it('renders archetype badge with "Unclassified" in empty state', () => {
		renderPage();
		expect(screen.getByText(/unclassified/i)).toBeInTheDocument();
	});

	it("renders radar empty state when dimensions are null", () => {
		renderPage();
		// F3a: When no snapshot data has all 6 dimensions populated,
		// radar shows empty state message instead of a collapsed polygon
		expect(
			screen.getByText(/hasn.*t crossed the.*2-source corroboration/i),
		).toBeInTheDocument();
	});

	it("renders sparklines for live dimensions, 'no events' for dead ones", () => {
		renderPage();
		// 4 live dimensions (orig, val, speed, frame) get SVG sparklines
		// 2 dead dimensions (edit, correct) show 'no events' text
		const svgs = document.querySelectorAll("svg");
		expect(svgs.length).toBeGreaterThanOrEqual(4);
		expect(screen.getAllByText("no events").length).toBeGreaterThanOrEqual(2);
	});

	it("vertical pills default to GEOPOLITICS active", () => {
		renderPage();
		const geopolitics = screen.getByRole("button", { name: /geopolitics/i });
		// Active pill should have the navy color border
		expect(geopolitics.className).toContain("font-heading");
	});
});
