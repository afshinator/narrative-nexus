import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import SettingsPage from "../pages/Settings";

// Wrap in MemoryRouter since SettingsPage doesn't need BrowserRouter
function renderSettings() {
  return render(
    <MemoryRouter>
      <SettingsPage />
    </MemoryRouter>,
  );
}

describe("Settings Page", () => {
  beforeEach(async () => {
    const { useStore } = await import("../store");
    useStore.setState({
      consensusThresholds: {
        geopolitics: 65,
        economics: 75,
        technology: 75,
      },
      fontScale: 1.0,
      theme: "dark",
    });
  });

  describe("Consensus Thresholds section", () => {
    it("displays three threshold sliders with labels", () => {
      renderSettings();
      expect(screen.getByText(/geopolitics/i)).toBeInTheDocument();
      expect(screen.getByText(/economics/i)).toBeInTheDocument();
      expect(screen.getByText(/technology/i)).toBeInTheDocument();
    });

    it("displays threshold values in percent", () => {
      renderSettings();
      expect(screen.getByText(/65%/)).toBeInTheDocument();
    });

    it("has a reset button", () => {
      renderSettings();
      expect(
        screen.getByRole("button", { name: /reset/i }),
      ).toBeInTheDocument();
    });
  });

  describe("Font Scale section", () => {
    it("displays font scale slider", () => {
      renderSettings();
      expect(screen.getByText(/font scale/i)).toBeInTheDocument();
    });
  });

  describe("Theme section", () => {
    it("displays theme toggle", () => {
      renderSettings();
      expect(screen.getByText(/theme/i)).toBeInTheDocument();
    });
  });
});
