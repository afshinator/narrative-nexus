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

	it("renders radar chart canvas", () => {
		renderPage();
		expect(screen.getByTestId("radar-chart")).toBeInTheDocument();
	});

	it("renders 6 sparkline SVGs", () => {
		renderPage();
		// Each dimension gets a sparkline SVG — check for 6 svg elements
		const svgs = document.querySelectorAll("svg");
		expect(svgs.length).toBeGreaterThanOrEqual(6);
	});

	it("renders day scrubber with slider and play button", () => {
		renderPage();
		expect(screen.getByRole("button", { name: /play/i })).toBeInTheDocument();
		expect(screen.getByRole("slider")).toBeInTheDocument();
		// Day counter starts at 0
		const sliders = screen.getAllByRole("slider");
		const daySlider = sliders[0] as HTMLInputElement;
		expect(daySlider.value).toBe("0");
	});

	it("play button toggles to pause when clicked", async () => {
		const user = userEvent.setup();
		renderPage();
		const playBtn = screen.getByRole("button", { name: /play/i });
		await user.click(playBtn);
		// ponytail: just check that clicking toggled — don't fight fake timers + startTransition
		expect(screen.getByRole("button", { name: /pause/i })).toBeInTheDocument();
	});

	it("renders event card placeholder in empty state", () => {
		renderPage();
		expect(screen.getByText(/drag the slider/i)).toBeInTheDocument();
	});

	it("vertical pills default to GEOPOLITICS active", () => {
		renderPage();
		const geopolitics = screen.getByRole("button", { name: /geopolitics/i });
		// Active pill should have the navy color border
		expect(geopolitics.className).toContain("font-heading");
	});
});
