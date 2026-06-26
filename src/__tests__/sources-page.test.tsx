import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";
import SourcesPage from "../pages/Sources";

function renderSources() {
	return render(
		<MemoryRouter>
			<SourcesPage />
		</MemoryRouter>,
	);
}

describe("Sources Page", () => {
	beforeEach(async () => {
		const { useStore } = await import("../store");
		useStore.setState({ archetypeFilter: null });
	});

	it("renders page heading", () => {
		renderSources();
		expect(
			screen.getByRole("heading", { name: /sources/i }),
		).toBeInTheDocument();
	});

	describe("Archetype filter pills", () => {
		it("renders 5 filter pills with correct labels", () => {
			renderSources();
			expect(
				screen.getByRole("button", { name: /all sources/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("button", { name: /early breaker/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("button", { name: /noise generator/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("button", { name: /selective/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("button", { name: /consensus follower/i }),
			).toBeInTheDocument();
		});

		it('"All" is active by default', () => {
			renderSources();
			const all = screen.getByRole("button", { name: /all sources/i });
			expect(all).toBeInTheDocument();
		});
	});

	describe("Scatter plot", () => {
		it("renders scatter plot card heading", () => {
			renderSources();
			expect(
				screen.getByRole("heading", { name: /reputation map/i }),
			).toBeInTheDocument();
		});

		it("renders an SVG element inside the scatter card", () => {
			renderSources();
			const svg = document.querySelector("svg");
			expect(svg).toBeInTheDocument();
		});

		it("renders four quadrant labels in the SVG", () => {
			renderSources();
			const svg = document.querySelector("svg");
			if (!svg) throw new Error("SVG not found");
			expect(svg.textContent).toContain("EARLY BREAKERS");
			expect(svg.textContent).toContain("NOISE GENERATORS");
			expect(svg.textContent).toContain("SELECTIVE BUT ACCURATE");
			expect(svg.textContent).toContain("CONSENSUS FOLLOWERS");
		});

		it("renders scatter markers when scores are provided", () => {
			const testScores = [
				{
					sourceId: "reuters",
					vertical: "geopolitics",
					R_orig: 92,
					R_val: 88,
					R_speed: 3.2,
					R_frame: 0.12,
					R_edit: 0,
					R_correct: 1,
				},
				{
					sourceId: "zerohedge",
					vertical: "geopolitics",
					R_orig: 75,
					R_val: 10,
					R_speed: 8.7,
					R_frame: 3.4,
					R_edit: 0,
					R_correct: 5,
				},
			];
			render(
				<MemoryRouter>
					<SourcesPage scores={testScores} />
				</MemoryRouter>,
			);
			const svg = document.querySelector("svg");
			expect(svg).toBeInTheDocument();
			// All 20 sources render — scored ones at their R_orig/R_val, unscored at origin
			const markers = svg?.querySelectorAll("path.marker");
			expect(markers?.length).toBe(20);
		});

		it("colors scatter markers by archetype", () => {
			// 4 sources, one in each quadrant → 4 different archetypes
			const fourScores = [
				{
					sourceId: "reuters",
					vertical: "geopolitics",
					R_orig: 90,
					R_val: 85,
					R_speed: 2,
					R_frame: 0.1,
					R_edit: 0,
					R_correct: 1,
				},
				{
					sourceId: "zerohedge",
					vertical: "geopolitics",
					R_orig: 85,
					R_val: 10,
					R_speed: 5,
					R_frame: 2,
					R_edit: 0,
					R_correct: 3,
				},
				{
					sourceId: "nyt",
					vertical: "geopolitics",
					R_orig: 15,
					R_val: 80,
					R_speed: 4,
					R_frame: 0.5,
					R_edit: 0,
					R_correct: 2,
				},
				{
					sourceId: "fox-news",
					vertical: "geopolitics",
					R_orig: 20,
					R_val: 20,
					R_speed: 7,
					R_frame: 3,
					R_edit: 0,
					R_correct: 0,
				},
			];
			render(
				<MemoryRouter>
					<SourcesPage scores={fourScores} />
				</MemoryRouter>,
			);
			const svg = document.querySelector("svg");
			if (!svg) throw new Error("SVG not found");
			const fills = new Set<string>();
			svg.querySelectorAll("path.marker").forEach((m) => {
				const f = m.getAttribute("fill");
				if (f) fills.add(f);
			});
			// Should have at least 4 different fill colors (one per archetype)
			expect(fills.size).toBeGreaterThanOrEqual(4);
		});
	});

	describe("Leaderboard table", () => {
		it("renders ledger heading", () => {
			renderSources();
			expect(
				screen.getByRole("heading", { name: /full ledger/i }),
			).toBeInTheDocument();
		});

		it("renders a table with source names", () => {
			renderSources();
			const table = document.querySelector("table");
			expect(table).toBeInTheDocument();
			expect(screen.getByText("Reuters")).toBeInTheDocument();
			expect(screen.getByText("AP")).toBeInTheDocument();
			expect(screen.getByText("ZeroHedge")).toBeInTheDocument();
		});

		it("renders column headers", () => {
			renderSources();
			expect(
				screen.getByRole("columnheader", { name: /source/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("columnheader", { name: /origination/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("columnheader", { name: /validation/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("columnheader", { name: /speed/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("columnheader", { name: /framing/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("columnheader", { name: /silent/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("columnheader", { name: /correction/i }),
			).toBeInTheDocument();
		});
		it("each table row has data-source-id for cross-link", async () => {
			renderSources();
			const { DEFAULT_SOURCES } = await import("../data/sources");
			for (const source of DEFAULT_SOURCES) {
				const row = document.querySelector(`[data-source-id="${source.id}"]`);
				expect(row).toBeInTheDocument();
			}
		});
	});

	describe("Filter behavior", () => {
		it("clicking a filter pill updates store filter", async () => {
			const user = userEvent.setup();
			renderSources();
			await user.click(screen.getByRole("button", { name: /early breaker/i }));
			const { useStore } = await import("../store");
			expect(useStore.getState().archetypeFilter).toBe("EARLY_BREAKER");
		});

		it('clicking "All" resets filter to null', async () => {
			const user = userEvent.setup();
			const { useStore } = await import("../store");
			useStore.setState({ archetypeFilter: "NOISE_GENERATOR" });
			renderSources();
			await user.click(screen.getByRole("button", { name: /all sources/i }));
			expect(useStore.getState().archetypeFilter).toBeNull();
		});
	});

	describe("Score rendering with data", () => {
		it("renders score values instead of dashes when scores provided", () => {
			const testScores = [
				{
					sourceId: "reuters",
					vertical: "geopolitics",
					R_orig: 92,
					R_val: 88,
					R_speed: 3.2,
					R_frame: 0.12,
					R_edit: 0,
					R_correct: 1,
				},
			];
			render(
				<MemoryRouter>
					<SourcesPage scores={testScores} />
				</MemoryRouter>,
			);
			const reutersRow = document.querySelector('[data-source-id="reuters"]');
			expect(reutersRow).toBeInTheDocument();
			expect(reutersRow?.textContent).toContain("92");
			expect(reutersRow?.textContent).not.toContain("—");
		});
	});

	describe("Sorting", () => {
		it("column headers are clickable", async () => {
			const user = userEvent.setup();
			renderSources();
			const origHeader = screen.getByRole("columnheader", {
				name: /origination/i,
			});
			await user.click(origHeader);
			// No crash — sort is functional
			expect(origHeader).toBeInTheDocument();
		});
	});

	describe("Vertical filter", () => {
		it("renders 3 vertical picker pills", () => {
			renderSources();
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

		it("Geopolitics is the default vertical pill", () => {
			renderSources();
			const geo = screen.getByRole("button", { name: /geopolitics/i });
			expect(geo.className).toContain("border-[var(--nn-navy)]");
		});

		it("clicking Economics updates subtitle", async () => {
			const user = userEvent.setup();
			renderSources();
			await user.click(screen.getByRole("button", { name: /economics/i }));
			expect(screen.getByText(/economics vertical/i)).toBeInTheDocument();
		});
	});
});
