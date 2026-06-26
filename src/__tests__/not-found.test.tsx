import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import NotFoundPage from "../pages/NotFound";

function renderPage() {
	return render(
		<MemoryRouter>
			<NotFoundPage />
		</MemoryRouter>,
	);
}

describe("NotFound Page", () => {
	it("renders 'Page not found' heading", () => {
		renderPage();
		expect(
			screen.getByRole("heading", { name: /page not found/i }),
		).toBeInTheDocument();
	});

	it("renders a descriptive message", () => {
		renderPage();
		expect(screen.getByText(/looking for/i)).toBeInTheDocument();
	});

	it("renders a link back to Sources", () => {
		renderPage();
		expect(
			screen.getByRole("link", { name: /back to sources/i }),
		).toBeInTheDocument();
	});
});
