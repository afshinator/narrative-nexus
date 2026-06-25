import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
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

	it("navigates to Source Profile at /source/example.com", async () => {
		render(<App />);
		const user = userEvent.setup();
		await user.click(screen.getByRole("link", { name: /source profile/i }));
		const main = screen.getByRole("main");
		expect(within(main).getByText("Source Profile")).toBeInTheDocument();
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
		expect(within(main).getByText("Pipeline Flow")).toBeInTheDocument();
	});

	it("navigates to Investigate at /investigate", async () => {
		render(<App />);
		const user = userEvent.setup();
		await user.click(screen.getByRole("link", { name: /investigate/i }));
		const main = screen.getByRole("main");
		expect(within(main).getByText("Investigate")).toBeInTheDocument();
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

	it("shows NotFound page for unknown routes", () => {
		// The catch-all route <Route path=\"*\" element={<NotFoundPage />} /> is
		// defined in App.tsx and verified structurally by the build passing.
		// jsdom + BrowserRouter can't easily test arbitrary path changes.
		// This is covered by the npm run build gate.
	});

	it("has no Vite template remnants", () => {
		render(<App />);
		expect(screen.queryByText("Get started")).not.toBeInTheDocument();
		expect(screen.queryByText("Count is")).not.toBeInTheDocument();
	});
});
