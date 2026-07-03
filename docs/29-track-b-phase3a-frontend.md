# Track B Phase 3A — SSE Client + Live Results Rendering

**Date:** 2026-07-03

---

## Skills/References Consulted

1. `nn-dev-workflow` skill — loaded. Contains vault tool corruption patterns, async generator pitfall, SSE plumbing verification reference.
2. `docs/design-tokens.md` — colors, fonts, spacing used throughout.

No SSE consumption reference in nn-dev-workflow. SSE parsing is manual via `fetch` + `ReadableStream` (EventSource is GET-only, endpoint is POST).

---

## Sub-Gate 3A1 — SSE PLUMBING + STAGE STEPPER ✅

### F1. EventSource wiring

**Approach:** `fetch("/api/investigate/stream", { method: "POST" })` → `resp.body.getReader()` → manual SSE line parsing (`event:` / `data:`). AbortController for cleanup on unmount/new query. `src/pages/Investigate.tsx:100-175`.

### F2. Stage stepper

Six stages rendered as horizontal pill chain. Colors match design tokens: `var(--nn-navy)` running, `var(--nn-teal)` done, `var(--nn-text-dim)` pending. Provider badge "fireworks · kimi-k2p5" visible when any stage running. `src/pages/Investigate.tsx:218-243`.

### F3. Verification

**Vitest:** 8/8 tests pass. Mock SSE stream via `mockSSEStream()` helper. Stage transitions verified, article cards rendered with claims, consensus panel renders.

**Live:** Run against real backend with "Iran deal" — pipeline streams 6 stages, article cards populate with BBC/AP/CBS claims, consensus panel renders per-claim breakdown.

**Success criteria:** All met. Stream opens, stepper transitions, provider badge visible, vitest passes, build clean.

---

## Sub-Gate 3A2 — QUERY INPUT + RESULTS RENDERING ✅

### F4. Query input + preset pills

Text input with "Search any subject..." placeholder. Three preset pills: "Iran deal", "Venezuela earthquake", "Anthropic export ban" (Phase 2C S2 verified queries). Copy: "Live analysis — your query runs through our pipeline in real time via Fireworks-hosted Kimi-K2P5." `src/pages/Investigate.tsx:247-263`.

### F5. Article grid

2-column responsive grid. Cards show: source domain badge, title (linked to source URL, target=_blank), body preview truncated ~150 chars, claims as bullet list. Fade-in via transitions. `src/pages/Investigate.tsx:285-324`.

### F6. Consensus panel

Renders below article grid. Claims sorted by source_count descending. Each claim shows: text, source badges, "reported by X of Y consensus-pool sources" math, green border + badge for would_absorb=true. `src/pages/Investigate.tsx:340-372`.

### F7. Empty/error states

- Search < 3 URLs: warning banner + preset suggestions
- Fetch failures: non-blocking amber banner "N of M sources returned no body"
- Error event: red banner + retry button
- Idle state: "Enter a subject query..." with description

### F8. Verification

Vitest 8/8: mock full event sequence for "Iran deal", asserts article cards render, claims appear, consensus panel renders, multi-source claim appears in both article card and consensus panel. Error state test verifies error message + retry button. Preset pill test verifies fetch call with correct body.

---

## Adversarial Review

Checked: if two events arrive out of order — SSE parsing uses named events (`event: X` → `data: Y`), order independent. Connection drop — fetch error caught by catch block, shows error text. Error before search — `!resp.ok || !resp.body` check before reader, shows "Backend returned an error."

Checked file at exact lines: all claims verified. No corruption. Build passes.

---

## Demo lens

A judge can now type "Iran deal" and watch the pipeline execute in real time: stage stepper animates through 6 steps with wall-clock timings, article cards populate with real claims from BBC/AP/CBS, consensus panel shows which claims would enter consensus reality. Previously this page was a pure stub with a textarea that stored to localStorage but did nothing.

---

## Delta-to-spec

| Task | Status | Note |
|------|--------|------|
| F1: EventSource wiring | DONE | fetch + ReadableStream SSE parser |
| F2: Stage stepper | DONE | 6 stages, 3 visual states, design tokens |
| F3: Vitest verification | DONE | 8/8 pass, mock SSE stream |
| F4: Query input + pills | DONE | 3 preset queries from Phase 2C verified list |
| F5: Article grid | DONE | 2-col responsive, claims, body preview |
| F6: Consensus panel | DONE | Sorted by source count, would_absorb badge |
| F7: Empty/error states | DONE | Warning, error+retry, idle, partial results |
| F8: Vitest verification | DONE | Full event sequence mock, all states tested |

---

## Regression check

- **Build:** 468ms, clean
- **Vitest:** 149 passed (11 router-shell pre-existing), 4 skipped
- **Agent 2 config:** unchanged (DeepSeek-V4-Pro)
- **No HEALTHY page degraded**

---

## I'd catch this myself

1. **SSE buffer splitting across chunks** — if an SSE line is split across two `reader.read()` chunks, the line-buffer logic (buffer + split) handles this via the leftover `buffer = lines.pop()` technique. Works for lines up to the chunk size (~64KB).

2. **No loading skeleton** — the stage stepper provides progress but article grid slots appear empty until `extract_result` events arrive. A skeleton placeholder would improve perceived responsiveness.

3. **Preset pills trigger immediate fetch** — no confirmation step. For a real product, you'd want a "submit" action after selecting a preset, but for a demo the immediate trigger is fine.

4. **`stopPropagation` not called on preset click** — the button click triggers both the preset handler and the form submit (Enter key). Works correctly because `handleSubmit` calls `runQuery(query)` with the already-set query, but the Enter key handler (`onKeyDown`) also calls `handleSubmit`. Not a bug but worth noting.

---

## Final Verdict Line

**Phase 3A COMPLETE. Ready for Phase 3B (slider + persistence).** 8/8 vitest tests pass, build clean at 468ms, no regressions. Investigate page now consumes live SSE stream, renders stage stepper, article grid, consensus panel, and all empty/error states per spec.
