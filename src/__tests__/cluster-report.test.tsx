import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ClusterReportPage from "../pages/ClusterReport";

const mockData = {
	cluster: { id: 1, title: "Test Cluster", vertical: "geopolitics" },
	summary: { totalClaims: 5, absorbed: 3, pending: 2, sourceCount: 2 },
	sources: [
		{ domain: "reuters.com", tier: 1, claims: 3, absorbed: 2, pending: 1 },
		{ domain: "bbc.com", tier: 1, claims: 2, absorbed: 1, pending: 1 },
	],
	claims: [
		{
			id: 1,
			text: "Claim one",
			state: "CONSENSUS_ABSORBED",
			absorbed_at: "2026-06-01T00:00:00Z",
			created_at: "2026-06-01T00:00:00Z",
			domains: ["reuters.com"],
		},
		{
			id: 2,
			text: "Claim two",
			state: "PENDING",
			absorbed_at: null,
			created_at: "2026-06-01T00:00:00Z",
			domains: ["bbc.com"],
		},
	],
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
		<MemoryRouter initialEntries={[`/clusters/${clusterId}/report`]}>
			<Routes>
				<Route
					path="/clusters/:clusterId/report"
					element={<ClusterReportPage />}
				/>
			</Routes>
		</MemoryRouter>,
	);
}

describe("ClusterReport Page", () => {
	beforeEach(() => {
		vi.restoreAllMocks();
	});

	it("shows loading state before fetch resolves", () => {
		// ponytail: no fetch mock = promise never resolves = loading forever
		renderPage();
		expect(
			screen.getByRole("heading", { name: /cluster report/i }),
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

	it("renders header with cluster title", async () => {
		mockFetch(mockData);
		renderPage();
		await waitFor(() =>
			expect(screen.getByText("Test Cluster")).toBeInTheDocument(),
		);
	});

	it("renders consensus summary stats", async () => {
		mockFetch(mockData);
		renderPage();
		await waitFor(() =>
			expect(screen.getByText(/consensus summary/i)).toBeInTheDocument(),
		);
		// "5" (totalClaims) appears in both Consensus Summary and Coverage blocks
		expect(screen.getAllByText("5").length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(3);
		expect(screen.getAllByText("3").length).toBeGreaterThanOrEqual(2);
	});

	it("renders source breakdown table", async () => {
		mockFetch(mockData);
		renderPage();
		await waitFor(() =>
			expect(
				screen.getByRole("heading", { name: /source breakdown/i }),
			).toBeInTheDocument(),
		);
		expect(screen.getAllByText("reuters.com").length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText("bbc.com").length).toBeGreaterThanOrEqual(1);
	});

	it("renders claims table", async () => {
		mockFetch(mockData);
		renderPage();
		await waitFor(() =>
			expect(
				screen.getByRole("heading", { name: "Claims" }),
			).toBeInTheDocument(),
		);
		expect(screen.getByText("Claim one")).toBeInTheDocument();
		expect(screen.getByText("Claim two")).toBeInTheDocument();
	});

	it("renders forensic analysis placeholder", async () => {
		mockFetch(mockData);
		renderPage();
		await waitFor(() =>
			expect(screen.getByText(/forensic analysis/i)).toBeInTheDocument(),
		);
		expect(
			screen.getByText(/convergence-type data is not yet computed/i),
		).toBeInTheDocument();
	});
});
