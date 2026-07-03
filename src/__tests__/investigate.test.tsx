import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import InvestigatePage from "../pages/Investigate";

function renderPage() {
  const user = userEvent.setup();
  return { user, ...render(<MemoryRouter><InvestigatePage /></MemoryRouter>) };
}

function mockSSEStream(events: Array<{ event: string; data: unknown }>) {
  const lines = events.flatMap((e) => [`event: ${e.event}`, `data: ${JSON.stringify(e.data)}`, ""]);
  const body = new ReadableStream({ start(c) { c.enqueue(new TextEncoder().encode(lines.join("\n"))); c.close(); } });
  return Promise.resolve({ ok: true, body } as Response);
}

describe("Investigate Page", () => {
  beforeEach(() => { vi.restoreAllMocks(); localStorage.clear(); });

  it("renders heading, input, Analyze, presets, idle state", () => {
    renderPage();
    expect(screen.getByRole("heading", { name: /investigate/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search any subject/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /analyze/i })).toBeInTheDocument();
    expect(screen.getByText("Iran deal")).toBeInTheDocument();
    expect(screen.getByText("Venezuela earthquake")).toBeInTheDocument();
    expect(screen.getByText(/enter a subject query/i)).toBeInTheDocument();
  });

  it("renders stage stepper with 6 stages", () => {
    renderPage();
    for (const s of ["Search","Fetch","Embed","Extract","Match","Consensus"])
      expect(screen.getByText(s)).toBeInTheDocument();
  });

  it("streams SSE events and renders articles + consensus + slider", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(mockSSEStream([
      { event: "stage_start", data: { stage: "search", index: 1, total: 6 } },
      { event: "search_result", data: { urls: [{ title: "Iran deal", url: "https://bbc.com/1", source_domain: "bbc.com" }] } },
      { event: "fetch_progress", data: { url: "https://bbc.com/1", body: "Body text.", status: "ok" } },
      { event: "extract_result", data: { url: "https://bbc.com/1", source_domain: "bbc.com", claims: [{ text: "Claim one.", entities: [] }, { text: "Claim two.", entities: [] }], framing_score: 3 } },
      { event: "match_result", data: { canonical_claims: [{ text: "Claim one.", source_count: 1, variants: [{ source: "bbc.com", article: "u", text: "Claim one." }] }] } },
      { event: "consensus_result", data: { per_claim: [{ claim_text: "Claim one.", source_count: 1, t1t2_reporting: 1, pool_size: 5, pct: 20, threshold: 65, would_absorb: false, would_need_for_absorption: "need 2" }, { claim_text: "Claim two.", source_count: 1, t1t2_reporting: 2, pool_size: 5, pct: 40, threshold: 65, would_absorb: false, would_need_for_absorption: "need 2" }], thresholds: {}, pool_size: 5, min_corroboration: 2 } },
      { event: "done", data: { total_ms: 3000 } },
    ]));

    const { user } = renderPage();
    await user.type(screen.getByPlaceholderText(/search any subject/i), "Iran deal");
    await user.click(screen.getByRole("button", { name: /analyze/i }));

    await waitFor(() => { expect(screen.getByText("Articles (1 analyzed)")).toBeInTheDocument(); });
    expect(screen.getByText("Consensus Analysis")).toBeInTheDocument();
    expect(screen.getByText("Consensus threshold — 65%")).toBeInTheDocument();
    // Slider is present (radix renders role=slider)
    expect(screen.getByRole("slider")).toBeInTheDocument();
  });

  it("slider renders with threshold label and caption", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(mockSSEStream([
      { event: "stage_start", data: { stage: "search" } },
      { event: "search_result", data: { urls: [{ title: "T", url: "u", source_domain: "bbc.com" }] } },
      { event: "fetch_progress", data: { url: "u", body: "B.", status: "ok" } },
      { event: "extract_result", data: { url: "u", source_domain: "bbc.com", claims: [{ text: "C.", entities: [] }], framing_score: 3 } },
      { event: "match_result", data: { canonical_claims: [{ text: "C.", source_count: 2, variants: [{ source: "bbc.com", article: "u", text: "C." }] }] } },
      { event: "consensus_result", data: { per_claim: [{ claim_text: "C.", source_count: 2, t1t2_reporting: 2, pool_size: 4, pct: 50, threshold: 65, would_absorb: false, would_need_for_absorption: "need 2" }], thresholds: {}, pool_size: 4, min_corroboration: 2 } },
      { event: "done", data: { total_ms: 2000 } },
    ]));
    const { user } = renderPage();
    await user.type(screen.getByPlaceholderText(/search any subject/i), "test");
    await user.click(screen.getByRole("button", { name: /analyze/i }));
    await waitFor(() => { expect(screen.getByText("Consensus threshold — 65%")).toBeInTheDocument(); });
    // Slider rendered
    expect(screen.getByRole("slider")).toBeInTheDocument();
    // Caption visible
    expect(screen.getByText(/consensus reality is a parameter/i)).toBeInTheDocument();
  });

  it("saves results to localStorage on done event", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(mockSSEStream([
      { event: "stage_start", data: { stage: "search" } },
      { event: "search_result", data: { urls: [{ title: "A", url: "u", source_domain: "bbc.com" }] } },
      { event: "fetch_progress", data: { url: "u", body: "B.", status: "ok" } },
      { event: "extract_result", data: { url: "u", source_domain: "bbc.com", claims: [{ text: "C.", entities: [] }], framing_score: 3 } },
      { event: "match_result", data: { canonical_claims: [{ text: "C.", source_count: 1, variants: [{ source: "bbc.com", article: "u", text: "C." }] }] } },
      { event: "consensus_result", data: { per_claim: [{ claim_text: "C.", source_count: 1, t1t2_reporting: 1, pool_size: 5, pct: 20, threshold: 65, would_absorb: false, would_need_for_absorption: "need 2" }], thresholds: {}, pool_size: 5, min_corroboration: 2 } },
      { event: "done", data: { total_ms: 3000 } },
    ]));
    const { user } = renderPage();
    await user.type(screen.getByPlaceholderText(/search any subject/i), "Iran deal");
    await user.click(screen.getByRole("button", { name: /analyze/i }));
    await waitFor(() => { expect(screen.getByText("Consensus Analysis")).toBeInTheDocument(); });

    // localStorage should have at least one entry
    const raw = localStorage.getItem("nn_investigate_history");
    expect(raw).not.toBeNull();
    const entries = JSON.parse(raw!);
    expect(entries.length).toBeGreaterThanOrEqual(1);
    expect(entries[0].query).toBe("Iran deal");
  });

  it("shows error and retry button on fetch failure", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Connection refused"));
    const { user } = renderPage();
    await user.type(screen.getByPlaceholderText(/search any subject/i), "test");
    await user.click(screen.getByRole("button", { name: /analyze/i }));
    await waitFor(() => { expect(screen.getByText("Connection refused")).toBeInTheDocument(); });
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });
});
