import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";
import PipelineFlowPage from "../pages/PipelineFlow";

function renderPage() {
	return render(
		<MemoryRouter>
			<PipelineFlowPage />
		</MemoryRouter>,
	);
}

describe("PipelineFlow Page", () => {
	beforeEach(async () => {
		const { useStore } = await import("../store");
		useStore.setState({ onboardingComplete: true });
	});

	it("renders page heading", () => {
		renderPage();
		expect(
			screen.getByRole("heading", { name: /pipeline flow/i }),
		).toBeInTheDocument();
	});

	it("renders subtitle about agent swarm", () => {
		renderPage();
		const matches = screen.getAllByText(/agent swarm/i);
		expect(matches.length).toBeGreaterThanOrEqual(1);
	});

	describe("Stage nodes", () => {
		it("renders 4 stage cards with agent names as headings", () => {
			renderPage();
			expect(
				screen.getByRole("heading", { name: /intake & clustering/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("heading", { name: /forensic extraction/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("heading", { name: /consensus alignment/i }),
			).toBeInTheDocument();
			expect(
				screen.getByRole("heading", { name: /silent auditor/i }),
			).toBeInTheDocument();
		});

		it("renders stage numbers 1 through 4", () => {
			renderPage();
			expect(screen.getByText("1")).toBeInTheDocument();
			expect(screen.getByText("2")).toBeInTheDocument();
			expect(screen.getByText("3")).toBeInTheDocument();
			expect(screen.getByText("4")).toBeInTheDocument();
		});
	});

	describe("Compute badges", () => {
		it("shows AMD GPU badge", () => {
			renderPage();
			const badges = screen.getAllByText(/amd gpu/i);
			expect(badges.length).toBeGreaterThanOrEqual(2); // legend + accordion
		});

		it("shows Fireworks API badge", () => {
			renderPage();
			const badges = screen.getAllByText(/fireworks api/i);
			expect(badges.length).toBeGreaterThanOrEqual(3); // legend + 2 accordions
		});

		it("shows CPU badge", () => {
			renderPage();
			const cpuBadges = screen.getAllByText("CPU");
			expect(cpuBadges.length).toBeGreaterThanOrEqual(1);
		});
	});

	describe("Entry and exit nodes", () => {
		it("renders RSS/article ingest entry point", () => {
			renderPage();
			expect(screen.getByText(/article ingest/i)).toBeInTheDocument();
		});

		it("renders database exit point", () => {
			renderPage();
			expect(screen.getByText(/database/i)).toBeInTheDocument();
		});
	});

	describe("Connectors", () => {
		it("renders visual connectors between stages", () => {
			renderPage();
			// Connectors have SVG chevron arrows — find them by the aria-hidden SVGs
			const arrows = document.querySelectorAll(
				'svg[aria-hidden="true"] path[d="M2 2 L7 7 L12 2"]',
			);
			expect(arrows.length).toBe(5);
		});
	});

	describe("Offline status", () => {
		it("shows pipeline offline message", () => {
			renderPage();
			expect(screen.getByText(/pipeline offline/i)).toBeInTheDocument();
		});
	});
});
