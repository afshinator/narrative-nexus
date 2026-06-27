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

	describe("Scraper controls", () => {
		it("shows Start button (disabled) and fetches status on mount", async () => {
			const fetchMock = vi.fn().mockResolvedValueOnce({
				ok: true,
				json: () =>
					Promise.resolve({
						running: false,
						last_run: null,
						articles_inserted: 0,
					}),
			});
			vi.stubGlobal("fetch", fetchMock);

			renderPage();

			const btn = screen.getByRole("button", { name: /start/i });
			expect(btn).toBeInTheDocument();

			expect(fetchMock).toHaveBeenCalledWith("/api/scraper/status");
		});

		it("shows Stop button and article count when running", async () => {
			const fetchMock = vi.fn().mockResolvedValueOnce({
				ok: true,
				json: () =>
					Promise.resolve({
						running: true,
						last_run: "2026-06-26T14:30:00Z",
						articles_inserted: 142,
					}),
			});
			vi.stubGlobal("fetch", fetchMock);

			renderPage();

			await waitFor(() => {
				expect(screen.getByRole("button", { name: /stop/i })).toBeInTheDocument();
			});

			expect(screen.getByText(/142 articles/i)).toBeInTheDocument();
		});

		it("sends POST /api/scraper/start on Start click and updates UI", async () => {
			const fetchMock = vi
				.fn()
				.mockResolvedValueOnce({
					ok: true,
					json: () =>
						Promise.resolve({ running: false, last_run: null, articles_inserted: 0 }),
				})
				.mockResolvedValueOnce({
					ok: true,
					json: () => Promise.resolve({ status: "started" }),
				})
				.mockResolvedValueOnce({
					ok: true,
					json: () =>
						Promise.resolve({
							running: true,
							last_run: "2026-06-26T14:30:00Z",
							articles_inserted: 142,
						}),
				});
			vi.stubGlobal("fetch", fetchMock);

			const { user } = renderPage();

			await waitFor(() => {
				expect(screen.getByRole("button", { name: /start/i })).toBeInTheDocument();
			});

			await user.click(screen.getByRole("button", { name: /start/i }));

			expect(fetchMock).toHaveBeenCalledWith("/api/scraper/start", {
				method: "POST",
			});

			// Should re-fetch and show running state (review-03 adversarial F10)
			await waitFor(() => {
				expect(screen.getByRole("button", { name: /stop/i })).toBeInTheDocument();
			});
		});

		it("sends POST /api/scraper/stop on Stop click", async () => {
			const fetchMock = vi
				.fn()
				.mockResolvedValueOnce({
					ok: true,
					json: () =>
						Promise.resolve({
							running: true,
							last_run: "2026-06-26T14:30:00Z",
							articles_inserted: 142,
						}),
				})
				.mockResolvedValueOnce({
					ok: true,
					json: () => Promise.resolve({ status: "stopped" }),
				})
				.mockResolvedValueOnce({
					ok: true,
					json: () =>
						Promise.resolve({ running: false, last_run: null, articles_inserted: 142 }),
				});
			vi.stubGlobal("fetch", fetchMock);

			const { user } = renderPage();

			await waitFor(() => {
				expect(screen.getByRole("button", { name: /stop/i })).toBeInTheDocument();
			});

			await user.click(screen.getByRole("button", { name: /stop/i }));

			expect(fetchMock).toHaveBeenCalledWith("/api/scraper/stop", {
				method: "POST",
			});
		});

		it("shows and auto-clears error message on failed POST", async () => {
			const fetchMock = vi
				.fn()
				.mockResolvedValueOnce({
					ok: true,
					json: () =>
						Promise.resolve({ running: false, last_run: null, articles_inserted: 0 }),
				})
				.mockRejectedValueOnce(new Error("Network error"));
			vi.stubGlobal("fetch", fetchMock);

			const { user } = renderPage();

			await waitFor(() => {
				expect(screen.getByRole("button", { name: /start/i })).toBeInTheDocument();
			});

			await user.click(screen.getByRole("button", { name: /start/i }));

			await waitFor(() => {
				expect(screen.getByText(/failed/i)).toBeInTheDocument();
			});

			// Error auto-clears after 3s — wait with generous timeout (review-03 adversarial F6)
			await waitFor(
				() => {
					expect(screen.queryByText(/failed/i)).not.toBeInTheDocument();
				},
				{ timeout: 5000 },
			);
		});
	});
});
