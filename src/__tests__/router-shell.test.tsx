import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../App";

describe("Router Shell — Slice 0", () => {
	beforeEach(async () => {
		// jsdom's initial window.location is unreliable across environments.
		// Force it to "/" so the index route (Sources) is active.
		window.history.pushState({}, "", "/");
		// Suppress auto-opening onboarding dialog in router tests
		const { useStore } = await import("../store");
		useStore.setState({ onboardingComplete: true });
	});
	it("renders nav bar with 8 navigation links", () => {
		render(<App />);
		expect(screen.getByRole("link", { name: /sources/i })).toBeInTheDocument();
		expect(
			screen.getByRole("link", { name: /source profile/i }),
		).toBeInTheDocument();
		expect(
			screen.getByRole("link", { name: /cluster report/i }),
		).toBeInTheDocument();
		expect(screen.getByRole("link", { name: /timeline/i })).toBeInTheDocument();
		expect(screen.getByRole("link", { name: /pipeline/i })).toBeInTheDocument();
		expect(
			screen.getByRole("link", { name: /investigate/i }),
		).toBeInTheDocument();
		expect(screen.getByRole("link", { name: /panel/i })).toBeInTheDocument();
		expect(screen.getByRole("link", { name: /settings/i })).toBeInTheDocument();
	});

	it("renders Sources page at / (index route)", () => {
		render(<App />);
		const main = screen.getByRole("main");
		expect(within(main).getByText("Sources")).toBeInTheDocument();
	});

	it("navigates to Source Profile at /source/reuters.com — shows Reuters profile", async () => {
		render(<App />);
		const user = userEvent.setup();
		await user.click(screen.getByRole("link", { name: /source profile/i }));
		const main = screen.getByRole("main");
		expect(within(main).getByText("Reuters")).toBeInTheDocument();
	});

	it("navigates to Cluster Report at /cluster/abc123", async () => {
		render(<App />);
		const user = userEvent.setup();
		await user.click(screen.getByRole("link", { name: /cluster report/i }));
		const main = screen.getByRole("main");
		expect(within(main).getByText("Cluster Report")).toBeInTheDocument();
	});

	it("navigates to Timeline at /timeline/abc123", async () => {
		render(<App />);
		const user = userEvent.setup();
		await user.click(screen.getByRole("link", { name: /^timeline/i }));
		const main = screen.getByRole("main");
		expect(within(main).getByText("Timeline")).toBeInTheDocument();
	});

	it("navigates to Pipeline Flow at /pipeline", async () => {
		render(<App />);
		const user = userEvent.setup();
		await user.click(screen.getByRole("link", { name: /pipeline/i }));
		const main = screen.getByRole("main");
		expect(
			within(main).getByRole("heading", { name: /pipeline flow/i }),
		).toBeInTheDocument();
	});

	it("navigates to Investigate at /investigate", async () => {
		render(<App />);
		const user = userEvent.setup();
		await user.click(screen.getByRole("link", { name: /investigate/i }));
		const main = screen.getByRole("main");
		expect(
			within(main).getByRole("heading", { name: /investigate/i }),
		).toBeInTheDocument();
	});

	it("navigates to Panel at /panel", async () => {
		render(<App />);
		const user = userEvent.setup();
		await user.click(screen.getByRole("link", { name: /^panel/i }));
		const main = screen.getByRole("main");
		expect(within(main).getByText("Panel Management")).toBeInTheDocument();
	});

	it("navigates to Settings at /settings", async () => {
		render(<App />);
		const user = userEvent.setup();
		await user.click(screen.getByRole("link", { name: /settings/i }));
		const main = screen.getByRole("main");
		expect(within(main).getByText("Settings")).toBeInTheDocument();
	});

	it('active nav link has aria-current="page"', () => {
		render(<App />);
		const sourcesLink = screen.getByRole("link", {
			name: /^sources$/i,
			current: "page",
		});
		expect(sourcesLink).toBeInTheDocument();
		expect(sourcesLink).toHaveAttribute("aria-current", "page");
	});

	it("displays footer tagline on every page", () => {
		render(<App />);
		expect(
			screen.getByText(/narrative nexus tracks consensus reality, not truth/i),
		).toBeInTheDocument();
	});

	it("has no Vite template remnants", () => {
		render(<App />);
		expect(screen.queryByText("Get started")).not.toBeInTheDocument();
		expect(screen.queryByText("Count is")).not.toBeInTheDocument();
	});

	describe("Scraper status indicator", () => {
		beforeEach(() => {
			vi.restoreAllMocks();
		});

		it("shows a teal dot when scraper is running", async () => {
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

			render(<App />);

			const dot = await screen.findByTestId("scraper-status-dot");
			expect(dot).toBeInTheDocument();
			expect(dot.style.backgroundColor).toBe("var(--nn-teal)");
		});

		it("shows a slate dot when scraper is paused", async () => {
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

			render(<App />);

			const dot = await screen.findByTestId("scraper-status-dot");
			expect(dot).toBeInTheDocument();
			expect(dot.style.backgroundColor).toBe("var(--nn-slate)");
		});

		it("shows a dim dot when status fetch fails", async () => {
			const fetchMock = vi
				.fn()
				.mockRejectedValueOnce(new Error("Network error"));
			vi.stubGlobal("fetch", fetchMock);

			render(<App />);

			const dot = await screen.findByTestId("scraper-status-dot");
			expect(dot).toBeInTheDocument();
			expect(dot.style.backgroundColor).toBe("var(--nn-text-dim)");
		});
	});
});
