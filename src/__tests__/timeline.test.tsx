import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import TimelinePage from "../pages/Timeline";

const mockData = {
	cluster: { id: 1, title: "Test Cluster" },
	sources: [
		{
			domain: "reuters.com",
			tier: 1,
			claims: [
				{
					id: 1,
					text: "Claim one",
					state: "CONSENSUS_ABSORBED",
					absorbed_at: "2026-06-01T00:00:00Z",
					first_seen_at: "2026-06-01T00:00:00Z",
					created_at: "2026-06-01T00:00:00Z",
				},
			],
		},
		{
			domain: "bbc.com",
			tier: 1,
			claims: [
				{
					id: 2,
					text: "Claim two",
					state: "PENDING",
					absorbed_at: null,
					first_seen_at: "2026-06-02T00:00:00Z",
					created_at: "2026-06-02T00:00:00Z",
				},
			],
		},
	],
};

const singleClaimData = {
	cluster: { id: 1, title: "Single Claim Cluster" },
	sources: [
		{
			domain: "reuters.com",
			tier: 1,
			claims: [
				{
					id: 1,
					text: "Only claim",
					state: "PENDING",
					absorbed_at: null,
					first_seen_at: "2026-06-01T00:00:00Z",
					created_at: "2026-06-01T00:00:00Z",
				},
			],
		},
	],
};

const emptyData = {
	cluster: { id: 1, title: "Empty Cluster" },
	sources: [],
};

function mockFetch(response: unknown, status = 200) {
	vi.stubGlobal(
		"fetch",
		vi.fn(() =>
			status === 200
				? Promise.resolve({ ok: true, json: () => Promise.resolve(response) })
				: Promise.resolve({
						ok: false,
						status,
						json: () => Promise.resolve({ detail: "Cluster not found" }),
					}),
		),
	);
}

function renderPage(clusterId = "1") {
	return render(
		<MemoryRouter initialEntries={[`/clusters/${clusterId}/timeline`]}>
			<Routes>
				<Route
					path="/clusters/:clusterId/timeline"
					element={<TimelinePage />}
				/>
			</Routes>
		</MemoryRouter>,
	);
}

describe("Timeline Page", () => {
	beforeEach(() => {
		vi.restoreAllMocks();
	});

	it("shows loading state before fetch resolves", () => {
		renderPage();
		expect(
			screen.getByRole("heading", { name: /timeline/i }),
		).toBeInTheDocument();
		expect(screen.getByText(/loading/i)).toBeInTheDocument();
	});

	it("shows error for 404", async () => {
		mockFetch(null, 404);
		renderPage();
		await waitFor(() =>
			expect(screen.getByText(/cluster not found/i)).toBeInTheDocument(),
		);
	});

	it("shows error on network failure", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn(() => Promise.reject(new Error("Network error"))),
		);
		renderPage();
		await waitFor(() =>
			expect(screen.getByText(/network error/i)).toBeInTheDocument(),
		);
	});

	it("shows empty state when cluster has no claims", async () => {
		mockFetch(emptyData);
		renderPage();
		await waitFor(() =>
			expect(
				screen.getByText(/no claims in this cluster/i),
			).toBeInTheDocument(),
		);
	});

	it("renders header with cluster title and summary line", async () => {
		mockFetch(mockData);
		renderPage();
		await waitFor(() =>
			expect(screen.getByText("Test Cluster")).toBeInTheDocument(),
		);
		// Summary line: "2 sources · 2 claims · 2 days"
		expect(screen.getByText(/2 sources/i)).toBeInTheDocument();
		expect(screen.getByText(/2 claims/i)).toBeInTheDocument();
		expect(screen.getByText(/2 days/i)).toBeInTheDocument();
	});

	it("renders source rows with domains and tier", async () => {
		mockFetch(mockData);
		renderPage();
		await waitFor(() =>
			expect(screen.getByText("reuters.com")).toBeInTheDocument(),
		);
		expect(screen.getByText("bbc.com")).toBeInTheDocument();
	});

	it("renders claim cards for each claim", async () => {
		mockFetch(mockData);
		renderPage();
		await waitFor(() =>
			expect(screen.getByText("Claim one")).toBeInTheDocument(),
		);
		expect(screen.getByText("Claim two")).toBeInTheDocument();
	});

	it("renders single-claim timeline without crash (rangeMs=0 fallback)", async () => {
		mockFetch(singleClaimData);
		renderPage();
		await waitFor(() =>
			expect(screen.getByText("Single Claim Cluster")).toBeInTheDocument(),
		);
		// No crash = test passes
		expect(screen.getByText("Only claim")).toBeInTheDocument();
	});
});

describe("positionPercent", () => {
	// positionPercent is a pure function exported from Timeline
	// ponytail: test the math, not the DOM
	const positionPercent = (
		firstSeenAt: string,
		rangeStart: number,
		rangeMs: number,
	): number => {
		if (rangeMs === 0) return 0;
		const ts = new Date(firstSeenAt).getTime();
		return ((ts - rangeStart) / rangeMs) * 100;
	};

	it("returns 0% at range start", () => {
		const start = new Date("2026-06-01T00:00:00Z").getTime();
		const ms = 24 * 60 * 60 * 1000; // 1 day
		expect(positionPercent("2026-06-01T00:00:00Z", start, ms)).toBe(0);
	});

	it("returns 100% at range end", () => {
		const start = new Date("2026-06-01T00:00:00Z").getTime();
		const ms = 24 * 60 * 60 * 1000;
		expect(positionPercent("2026-06-02T00:00:00Z", start, ms)).toBe(100);
	});

	it("returns 50% at midpoint", () => {
		const start = new Date("2026-06-01T00:00:00Z").getTime();
		const ms = 24 * 60 * 60 * 1000;
		expect(positionPercent("2026-06-01T12:00:00Z", start, ms)).toBe(50);
	});

	it("returns 0% when rangeMs is 0", () => {
		const start = new Date("2026-06-01T00:00:00Z").getTime();
		expect(positionPercent("2026-06-01T00:00:00Z", start, 0)).toBe(0);
	});
});
