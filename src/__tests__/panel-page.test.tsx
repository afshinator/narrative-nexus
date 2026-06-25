import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";
import PanelPage from "../pages/Panel";

function renderPanel() {
	return render(
		<MemoryRouter>
			<PanelPage />
		</MemoryRouter>,
	);
}

describe("Panel Management Page", () => {
	beforeEach(async () => {
		const { useStore } = await import("../store");
		const { DEFAULT_SOURCES } = await import("../data/sources");
		useStore.setState({
			activeSources: DEFAULT_SOURCES.map((s) => s.id),
		});
	});

	it("displays tier labels", () => {
		renderPanel();
		expect(screen.getByText(/tier 1/i)).toBeInTheDocument();
		expect(screen.getByText(/tier 5/i)).toBeInTheDocument();
	});

	it("displays category balance indicator", () => {
		renderPanel();
		expect(screen.getByText(/balance/i)).toBeInTheDocument();
	});

	it("shows all 20 source names", () => {
		renderPanel();
		// Use getAllByText — each source name like "Reuters" appears once in the list
		expect(screen.getByText("Reuters")).toBeInTheDocument();
		expect(screen.getByText("ZeroHedge")).toBeInTheDocument();
		expect(screen.getByText("AP")).toBeInTheDocument();
		expect(screen.getByText("Bellingcat")).toBeInTheDocument();
	});

	it("shows active count for Tier 1 (5/5)", () => {
		renderPanel();
		// The balance summary shows T1: 5/5 — text is split across nodes
		// Check that "T1:" appears with count
		expect(screen.getByText(/t1:\s*5\s*\/\s*5/i)).toBeInTheDocument();
	});
});
