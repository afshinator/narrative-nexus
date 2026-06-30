import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import VfTrendChart from "../components/VfTrendChart";
import type { DailySnapshot } from "../data/scores";

// chart.js needs Canvas — jsdom doesn't have it
vi.mock("react-chartjs-2", () => ({
	Line: () => (
		<canvas data-testid="vf-trend-chart" aria-label="Vf trend chart" />
	),
}));

function makeSnapshot(day: number, r_val: number): DailySnapshot {
	return {
		sourceId: "1",
		vertical: "geopolitics",
		day,
		R_orig: 50,
		R_val: r_val,
		R_speed: 0,
		R_frame: 0,
		R_edit: 0,
		R_correct: 0,
	};
}

describe("VfTrendChart", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("renders empty state with no trend data message", () => {
		render(<VfTrendChart snapshots={[]} currentDay={0} />);
		expect(screen.getByText(/no trend data/i)).toBeInTheDocument();
	});

	it("renders with snapshots data", () => {
		const snapshots = [
			makeSnapshot(0, 50),
			makeSnapshot(1, 55),
			makeSnapshot(2, 60),
		];
		render(<VfTrendChart snapshots={snapshots} currentDay={1} />);
		expect(screen.getByTestId("vf-trend-chart")).toBeInTheDocument();
	});

	it("renders empty state when no snapshots", () => {
		render(<VfTrendChart snapshots={[]} currentDay={0} />);
		expect(screen.getByText(/no trend data/i)).toBeInTheDocument();
	});
});
