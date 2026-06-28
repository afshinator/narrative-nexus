import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PipelineFlowPage from "../pages/PipelineFlow";

function renderPage() {
	const user = userEvent.setup();
	return {
		user,
		...render(
			<MemoryRouter>
				<PipelineFlowPage />
			</MemoryRouter>,
		),
	};
}

/** Create a global fetch mock that handles provider config + scraper calls. */
function mockFetch(...scraperResponses: Array<unknown>) {
	let scraperIdx = 0;
	const fn = vi.fn((url: string, _init?: RequestInit) => {
		// Provider config calls
		if (url === "/api/config/providers/available") {
			return Promise.resolve({
				ok: true,
				json: () => Promise.resolve({
					providers: {
						embeddings: [{ id: "local-cpu", name: "Local CPU", model: "m", amd: false }],
						llm: [{ id: "opencode", name: "OpenCode Zen", model: "m", amd: false }],
					},
				}),
			});
		}
		if (url === "/api/config/providers") {
			return Promise.resolve({
				ok: true,
				json: () => Promise.resolve({
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
			json: () => Promise.resolve(resp ?? { running: false, last_run: null, articles_inserted: 0 }),
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
			for (const name of ["Intake & Clustering", "Forensic Extraction", "Consensus Alignment", "Silent Auditor"]) {
				expect(screen.getByRole("heading", { name: new RegExp(name, "i") })).toBeInTheDocument();
			}
		});

		it("renders stage numbers 1 through 4", () => {
			renderPage();
			for (const n of ["1", "2", "3", "4"]) {
				expect(screen.getByText(n)).toBeInTheDocument();
			}
		});
	});

	describe("Scraper controls", () => {
		it("shows Start button and fetches status on mount", async () => {
			mockFetch({ running: false, last_run: null, articles_inserted: 0 });
			renderPage();
			await waitFor(() => {
				expect(screen.getByRole("button", { name: /start/i })).toBeInTheDocument();
			});
		});

		it("shows Stop button and article count when running", async () => {
			mockFetch({ running: true, last_run: "2026-06-26T14:30:00Z", articles_inserted: 142 });
			renderPage();
			await waitFor(() => {
				expect(screen.getByRole("button", { name: /stop/i })).toBeInTheDocument();
			});
			expect(screen.getByText(/142 articles/i)).toBeInTheDocument();
		});

		it("sends POST /api/scraper/start on click and updates", async () => {
			const fn = mockFetch(
				{ running: false, last_run: null, articles_inserted: 0 },
				{ status: "started" },
				{ running: true, last_run: "Z", articles_inserted: 142 },
			);
			const { user } = renderPage();
			await waitFor(() => screen.getByRole("button", { name: /start/i }));
			await user.click(screen.getByRole("button", { name: /start/i }));
			expect(fn).toHaveBeenCalledWith("/api/scraper/start", { method: "POST" });
			await waitFor(() => screen.getByRole("button", { name: /stop/i }));
		});

		it("sends POST /api/scraper/stop on click", async () => {
			const fn = mockFetch(
				{ running: true, last_run: "Z", articles_inserted: 142 },
				{ status: "stopped" },
				{ running: false, last_run: null, articles_inserted: 142 },
			);
			const { user } = renderPage();
			await waitFor(() => screen.getByRole("button", { name: /stop/i }));
			await user.click(screen.getByRole("button", { name: /stop/i }));
			expect(fn).toHaveBeenCalledWith("/api/scraper/stop", { method: "POST" });
		});

		it("shows and auto-clears error on failed POST", async () => {
			const fn = mockFetch(
				{ running: false, last_run: null, articles_inserted: 0 },
				new Error("Network error"),
			);
			const { user } = renderPage();
			await waitFor(() => screen.getByRole("button", { name: /start/i }));
			await user.click(screen.getByRole("button", { name: /start/i }));
			await waitFor(() => expect(screen.getByText(/failed/i)).toBeInTheDocument());
			await waitFor(
				() => expect(screen.queryByText(/failed/i)).not.toBeInTheDocument(),
				{ timeout: 5000 },
			);
		});
	});
});
