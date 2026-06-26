import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { OnboardingDialog } from "../components/OnboardingDialog";

const TERMS = [
	"Consensus Reality",
	"Consensus-Absorbed",
	"Cross-Source Convergent",
	"Self-Consistent",
	"Unresolved",
	"Outlier Claim",
];

function renderDialog(open = true) {
	const user = userEvent.setup();
	return {
		user,
		...render(<OnboardingDialog open={open} onOpenChange={() => {}} />),
	};
}

describe("OnboardingDialog", () => {
	beforeEach(async () => {
		const { useStore } = await import("../store");
		useStore.setState({ onboardingComplete: false });
	});

	it("renders all 6 vocabulary terms with icons in a single view", () => {
		renderDialog();
		for (const term of TERMS) {
			expect(screen.getByText(term)).toBeInTheDocument();
		}
		// Each term heading has an icon (aria-hidden SVGs)
		const icons = document.querySelectorAll("h3 svg");
		expect(icons.length).toBe(6);
	});

	it('shows "Don\'t show on startup" checkbox', () => {
		renderDialog();
		expect(
			screen.getByRole("checkbox", { name: /don't show on startup/i }),
		).toBeInTheDocument();
	});

	it("sets onboardingComplete when checkbox is checked and dialog closed", async () => {
		const { user } = renderDialog();
		await user.click(
			screen.getByRole("checkbox", { name: /don't show on startup/i }),
		);
		await user.click(screen.getByRole("button", { name: /close/i }));

		const { useStore } = await import("../store");
		expect(useStore.getState().onboardingComplete).toBe(true);
	});

	it("does NOT set onboardingComplete when checkbox is unchecked and dialog closed", async () => {
		const { user } = renderDialog();
		await user.click(screen.getByRole("button", { name: /close/i }));

		const { useStore } = await import("../store");
		expect(useStore.getState().onboardingComplete).toBe(false);
	});

	it("closes dialog when Close button is clicked", async () => {
		const handleChange = vi.fn();
		const user = userEvent.setup();
		render(<OnboardingDialog open={true} onOpenChange={handleChange} />);
		await user.click(screen.getByRole("button", { name: /close/i }));
		expect(handleChange).toHaveBeenCalledWith(false);
	});
});
