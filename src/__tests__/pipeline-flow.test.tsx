import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PipelineFlowPage from "../pages/PipelineFlow";

function renderPage() {
	return render(
		<MemoryRouter>
			<PipelineFlowPage />
		</MemoryRouter>,
	);
}

/** Create a global fetch mock that handles provider config + scraper calls. */
function mockFetch(...scraperResponses: Array<unknown>) {
	let scraperIdx = 0;
	const fn = vi.fn((url: string, _init?: RequestInit) => {
		// Provider config calls
		if (url === "/api/config/providers/available") {
			return Promise.resolve({
				ok: true,
				json: () =>
					Promise.resolve({
						providers: {
							embeddings: [
								{ id: "local-cpu", name: "Local CPU", model: "m", amd: false },
							],
							llm: [
								{
									id: "opencode",
									name: "OpenCode Zen",
									model: "m",
									amd: false,
								},
							],
						},
					}),
			});
		}
		if (url === "/api/config/providers") {
			return Promise.resolve({
				ok: true,
				json: () =>
					Promise.resolve({
						providers: {
							agent1_embedding: "local-cpu",
							agent1_llm: "opencode",
							agent2_llm: "opencode",
							agent4_llm: "opencode",
						},
					}),
			});
		}
		// Scraper calls
		const resp = scraperResponses[scraperIdx++];
		if (resp instanceof Error) return Promise.reject(resp);
		return Promise.resolve({
			ok: true,
			json: () =>
				Promise.resolve(
					resp ?? { running: false, last_run: null, articles_inserted: 0 },
				),
		});
	});
	vi.stubGlobal("fetch", fn);
	return fn;
}

describe("PipelineFlow Page", () => {
	beforeEach(async () => {
		const { useStore } = await import("../store");
		useStore.setState({ onboardingComplete: true });
		vi.restoreAllMocks();
	});

	it("renders page heading", () => {
		renderPage();
		expect(
			screen.getByRole("heading", { name: /pipeline flow/i }),
		).toBeInTheDocument();
	});

	it("renders subtitle about configurable providers", () => {
		renderPage();
		expect(screen.getByText(/configurable per-stage/i)).toBeInTheDocument();
	});

	describe("Stage nodes", () => {
		it("renders 4 stage headings", () => {
			renderPage();
			for (const name of [
				"Intake & Clustering",
				"Forensic Extraction",
				"Consensus Alignment",
				"Silent Auditor",
			]) {
				expect(
					screen.getByRole("heading", { name: new RegExp(name, "i") }),
				).toBeInTheDocument();
			}
		});

		it("renders stage numbers 1 through 4", () => {
			renderPage();
			for (const n of ["1", "2", "3", "4"]) {
				expect(screen.getByText(n)).toBeInTheDocument();
			}
		});
	});

	describe("Scraper status card", () => {
		it("shows copy text on mount", async () => {
			renderPage();
			await waitFor(() =>
				expect(screen.getByText(/Scraper paused/i)).toBeInTheDocument(),
			);
		});

		it("no scraper button present (relocated to Settings — UX30)", () => {
			renderPage();
			expect(
				screen.queryByRole("button", { name: /start|stop/i }),
			).not.toBeInTheDocument();
		});
	});
});
