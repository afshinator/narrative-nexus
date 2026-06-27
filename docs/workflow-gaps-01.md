# Workflow & Specification Gaps — Review 03 Post-Mortem

**Date:** 2026-06-26  
**Source:** Findings from `docs/review-03.md` — adversarial review of all implemented code  
**Method:** Each finding from review-03 was traced back through the dev-workflow gates (Phase 3 Plan → Phase 3.5 Assumption Validation → Phase 4 Implement → Phase 5 Verify) to identify where the process failed to catch it. Recommendations focus on the workflow process, the spec document, and the design doc — not the code fixes.

---

## Gaps in the Dev-Workflow Process

### Gap 1: Phase 3.5 validates external deps but not cross-slice contracts

**Issue:** Assumption Validation checks each slice's external dependencies in isolation but doesn't validate data format contracts *between* slices. A producer slice and consumer slice written at different times can silently assume different formats.

**Findings this caused:**
- **C04/C05 (RSS date format):** Slice 8b (scraper) stores RSS dates as RFC 2822 strings from feedparser. Slice 8c (consensus agent) assumes all dates are ISO 8601 for `datetime.fromisoformat()`. Each slice validated its own deps; neither checked the format at the boundary between them.
- **H04 (Google News URLs):** Slice 8b validated that Google News RSS returns entries with titles and source domains — but didn't trace what happens when those opaque redirect URLs hit the `UNIQUE` constraint on `articles.url` or get rendered as frontend links.

**Fix:** Add a cross-slice boundary check sub-step to Phase 3.5:
> For every data flow that crosses a slice boundary (producer in one slice, consumer in a different slice), explicitly verify that the producer's output format matches the consumer's expected input format before implementation begins.

Checklist items:
- Date/time format (ISO 8601? RFC 2822? Unix timestamp?)
- URL format (canonical? redirect chain? relative vs absolute?)
- Null/value encoding (empty string vs None vs 0?)
- Number scale (0-1 vs 0-100 vs raw values?)

Current Phase 3.5 language in `CLAUDE.md`:
> "(a) verify every dependency and claim in the plan against the actual codebase/environment (fact-checking)"

This covers "does the API exist?" but not "does the output format of slice A match the input format expected by slice B?"

---

### Gap 2: Phase 3.5 validates at surface level, not through downstream impact

**Issue:** Assumption Validation passes when the immediate assertion holds (e.g., "RSS feed returns entries with URLs") but doesn't trace downstream consequences through the rest of the system.

**Findings this caused:**
- **H04 (Google News URLs):** The 8b plan explicitly documents the Google News tradeoff — "not possible for body extraction, entries get `body_status = 'BODY_UNAVAILABLE'`." But it never asked: "what does an opaque redirect URL do to the `UNIQUE` constraint on `articles.url`?" or "what happens when the frontend links to `news.google.com/articles/...` instead of `reuters.com/article/...`?"

**Fix:** Add a downstream-impact tracing step to Phase 3.5:
> For every external dependency tradeoff, list at least 3 downstream consequences before proceeding to implementation. If you cannot find 3 consequences, you haven't traced far enough.

Example for Google News URLs:
1. Body extraction impossible → BODY_UNAVAILABLE ✅ (already noted)
2. UNIQUE constraint on articles.url means same article gets re-inserted with different redirect URL → duplicates ✅ (not caught)
3. Frontend links to Google redirect URL instead of canonical article → broken links ✅ (not caught)

---

### Gap 3: Phase 5 Verify has no production-path integration test

**Issue:** The Verify checklist (`CLAUDE.md` line 17) includes `pytest`, `vitest run`, `npm run build`, `biome check` — all on test fixtures. There is no step that starts the app against a production-like configuration and verifies a real user flow.

**Findings this caused:**
- **C01 (API uses :memory: DB):** Every test uses an in-memory SQLite database. No test starts the FastAPI app with a real `data/nn.db` file and hits `/api/sources` to verify the route reads from the persistent store. The bug would be caught in 60 seconds by running `uvicorn` and making one curl call.
- **C02 (Schema crash on 2nd request):** Same root cause — no test connects to a persistent file and makes two requests. The schema loads on every connection, crashes on the second `CREATE TABLE` attempt.
- **T02 (Test asserts against wrong database):** The test creates its own `:memory:` database but asserts against the fixture's `:memory:` database (a different connection). No integration test catches this because no test uses a real file path.

**Fix:** Add a production-path verification step to Phase 5 Verify:
> Before running the full test suite, start the application with production configuration (real database file, real API keys if available, real env vars) and verify at least one primary user flow works end-to-end.

Checklist:
1. Start the app with a persistent SQLite file path
2. Hit each primary API endpoint and verify it returns data (not empty from `:memory:`)
3. Verify the app doesn't crash on the 2nd request to the same endpoint
4. Verify that data written by one route is readable by another

---

### Gap 4: Adversarial review reads code but doesn't trace user flows

**Issue:** The Phase 5a adversarial review starts by reading source files and checking against spec. This approach misses features where the code compiles, looks reasonable, but the primary user flow is disconnected.

**Findings this caused:**
- **C03 (Investigate query discarded):** Reading `handleSubmit()` in isolation, the missing `addAdHocResult()` call isn't visually obvious unless the reviewer is specifically looking for it. Tracing the user flow — "user types a query, clicks Submit, what happens?" — catches the bug in 10 seconds: the query disappears, a transient message shows, nothing is stored, nothing reaches the backend.
- **H05 (Sources vertical filter):** Reading the code, the `vertical` state is initialized, the `VerticalPills` component is rendered, the subtitle displays the selected vertical — everything looks wired up. Only by tracing "user clicks 'Economics' → what data changes in the scatter plot?" does the missing filter become visible.

**Fix:** Change adversarial review (Phase 5a) to start with flow tracing, not code reading:
> Before reading any source file, describe the primary user flow for this feature. Trace each step in order: what the user does → what the UI should show → what data flows where → what should change. Then check the code to see if that flow is actually implemented.

This is already partially implied in `CLAUDE.md` ("sanity-check the implementation end-to-end first") but the adversarial review procedure in the workflow skill (`workflow-skill/SKILL.md`) says "Receives: spec reqs for this slice + plan breakdown + code" — no mention of flow tracing.

---

### Gap 5: Phase 3 Plan grill doesn't flag spec ambiguities back to the source

**Issue:** The Plan phase says "Grill the plan — 'Prove this API exists. Show me the docs. What if it returns 500?'" This grills external dependency assumptions. But it doesn't separate "I made a design decision because the spec was ambiguous" from "the spec clearly says X and I'm implementing X."

**Findings this caused:**
- **H03 (Consensus denominator):** The design doc says "A claim enters the consensus baseline when it appears in more than threshold% of the pool's source graphs for that story." This is ambiguous — does "pool" mean "all T1+T2 sources" or "T1+T2 sources that covered this story"? The 8c plan's Decision 6 chose interpretation A (all T1+T2 sources) without flagging the ambiguity. This became the implemented behavior, and niche claims can never reach consensus because the denominator is too large.

**Fix:** Add to Phase 3 Plan:
> Before making a design decision that resolves a spec ambiguity, flag the ambiguity in the plan document and escalate it for clarification. Do not silently choose an interpretation. If the ambiguity is resolved in favor of one interpretation, update the spec to remove the ambiguity.

---

### Gap 6: No Verify step checks visual fidelity against design intent

**Issue:** The Verify phase checks tests, lint, typecheck, and spec coverage. For data-driven visualizations (colors, charts, graphs), no step checks that the visual output matches the design intent.

**Findings this caused:**
- **H01 (Polarity colors inverted):** `getPolarityColor()` was written as a simple threshold function (high=teal, medium=amber, low=red). It has no knowledge of which dimensions are inverted. CONTEXT.md documents the inversion for R_speed/R_frame/R_edit, but the color function never received that context. A visual check — "does a low R_speed (good) show as green?" — catches this immediately.
- **H02 (Tier average not inverted):** Same issue. The radar chart inverts current/baseline data but the tier average is plotted raw. A visual comparison — "do all three datasets use the same scale?" — catches the mismatch.

**Fix:** Add to Phase 5 Verify:
> For any slice that changes visual output (colors, charts, layout), verify the rendered result against design intent. Load the page with representative data and confirm: colors match dimension polarity, chart scales are consistent, empty states look intentional.

---

## Gaps in the Spec Document (`spec/requirements.md`)

### Spec Gap 1: REQ-022 — Consensus denominator is ambiguous

**Current text:**
> [desired] [REQ-022] The consensus baseline must be computed over Tier 1 and Tier 2 sources the consensus pool.

**Problem:** This doesn't specify whether the denominator is "all Tier 1+2 sources" or "Tier 1+2 sources that have at least one claim in the same cluster." The phrase "the consensus pool" is defined in the design doc as Tier 1+2 sources, but the analytical model in §4 says "% of the pool's source graphs **for that story**" — which suggests the denominator should be sources covering that story, not all sources.

**Suggested change:**
> [desired] [REQ-022] For each claim, the consensus baseline is the percentage of Tier 1+2 sources that have reported that specific claim, relative to the Tier 1+2 sources that have at least one claim in the same cluster (the sources covering that story). The denominator is not all Tier 1+2 sources — it is Tier 1+2 sources whose coverage scope overlaps with the cluster's topic.

---

### Spec Gap 2: REQ-082 — Polarity color behavior is underspecified

**Current text:**
> [desired] [REQ-082] Polarity binding must assign color by dimension using getPolarityColor.

**Problem:** This names a function but doesn't specify the behavior. The design doc (§4) defines three polarity categories — trait (neutral), graded-high-is-good (R_val), graded-low-is-good (R_speed, R_frame, R_edit) — but the requirement doesn't instruct the implementation to distinguish between them. A generic "high=green, medium=amber, low=red" function satisfies a literal reading of REQ-082 but violates the design intent for inverted dimensions.

**Suggested change:**
> [desired] [REQ-082] Polarity colors must reflect the dimension's favorable direction per the design doc §4:
> - Trait dimensions (R_orig, R_correct): neutral color (`--nn-slate`) regardless of value
> - Graded high-is-good (R_val,): green for high values (≥66), amber for medium (33-65), red for low (<33)
> - Graded low-is-good (R_speed, R_frame, R_edit): green for low values (<33), amber for medium (33-65), red for high (≥66)
> The color function must accept the dimension key and value, and apply inversion logic for low-is-good dimensions.

---

### Spec Gap 3: No requirement for API database path

**Current text:** None.

**Problem:** All API routes default to an in-memory database because there is no requirement forcing them to use the persistent file path. The design doc says "SQLite database — App server volume" but this was written as `[stack-bound]` (informational), not `[desired]` (enforceable by spec coverage).

**Suggested addition:**
> [desired] [REQ-123] API routes must read from and write to the persistent SQLite database file at the path specified by the `NN_DB_PATH` environment variable. Routes must not create or query in-memory databases unless explicitly in test code.

---

### Spec Gap 4: No requirement for vertical filtering on Sources page

**Current text:**
> [desired] [REQ-054] The system must support GEOPOLITICS vertical.
> [desired] [REQ-055] The system must support ECONOMICS vertical.
> [desired] [REQ-056] The system must support TECHNOLOGY vertical.

**Problem:** These requirements say verticals must be *supported* but don't say the Sources page must *filter by* vertical. The current Sources page has a vertical selector UI (pills + subtitle) but the data isn't filtered. The spec doesn't mandate filtering, so the missing data plumbing isn't a spec violation — it's an incomplete UX implementation.

**Suggested change to REQ-054:**
> [desired] [REQ-054] The system must support GEOPOLITICS vertical. The Sources page must filter displayed reputation scores by the selected vertical, showing only scores matching that vertical in both the scatter plot and the ledger table.

---

## Gaps in the Design Doc (`docs/design-v1.2.md`)

### Design Gap 1: No "Data Format Contracts" section

**Problem:** The design doc has System Architecture (§3) and Analytical Model (§4) but no section that defines data format contracts for system-wide concerns. Date format, URL format, number encoding, and null handling are left to each implementer's discretion, leading to the cross-slice format mismatches documented in C04/C05.

**Suggested addition to §3 (System Architecture):**

> **Data Format Contracts [LOCKED]**
>
> The following formats apply system-wide:
> - **Dates:** All dates stored in ISO 8601 format with UTC timezone (`YYYY-MM-DDTHH:MM:SS+00:00`). Feed dates from RSS (RFC 2822) must be converted before storage. `datetime.fromisoformat()` is the canonical Python parser.
> - **URLs:** All article URLs stored as canonical source URLs. Redirect chains must be resolved before storage. Google News redirect URLs must not be stored as-is — extract the original source URL from the redirect target.
> - **Numeric scales:** All percentage values normalized to 0-100. No 0-1 fractional values in the database.
> - **Nullable fields:** Dimensions not yet computable (R_frame, R_edit, R_correct until their respective agents are built) are stored as `NULL` in SQLite, not 0 or empty string. The frontend handles nulls gracefully (dashes, not zeros).

---

### Design Gap 2: Design doc §4 doesn't specify the consensus denominator scope

**Problem:** The analytical model says "A claim enters the consensus baseline when it appears in more than `threshold`% of the pool's source graphs for that story." The phrase "for that story" is ambiguous — it could mean "out of all T1+T2 source graphs that exist" or "out of T1+T2 source graphs that are relevant to this story."

**Suggested change to §4 (Consensus threshold):**

> The consensus baseline is computed over Tier 1+2 sources only (the "consensus pool"). A claim enters the consensus baseline when it appears in more than `threshold`% of the Tier 1+2 sources that have at least one claim in the same cluster. The denominator is not the total number of Tier 1+2 sources — it is the subset whose coverage scope overlaps with the cluster's topic. This prevents niche-coverage claims from being judged against sources that don't cover that subject matter.

---

## Summary: What to Change and Where

| What to change | Where | Which findings it prevents | Priority |
|---------------|-------|---------------------------|----------|
| Cross-slice boundary check in Phase 3.5 | `CLAUDE.md` + `workflow-skill/SKILL.md` | C04, C05, H04 (downstream) | High |
| Downstream-impact tracing in Phase 3.5 | `CLAUDE.md` + `workflow-skill/SKILL.md` | H04 (downstream), H03 | High |
| Production-path step in Phase 5 Verify | `CLAUDE.md` | C01, C02, T02 | High |
| Flow tracing in adversarial review (Phase 5a) | `workflow-skill/SKILL.md` | C03, H05 | Medium |
| Flag spec ambiguities in Phase 3 Plan | `CLAUDE.md` + `workflow-skill/SKILL.md` | H03 | Medium |
| Visual fidelity check in Phase 5 Verify | `CLAUDE.md` | H01, H02 | Medium |
| Tighten REQ-022 (consensus denominator) | `spec/requirements.md` | H03 | High |
| Tighten REQ-082 (polarity color behavior) | `spec/requirements.md` | H01 | High |
| Add REQ-123 (API database path) | `spec/requirements.md` | C01, C02 | High |
| Add vertical filtering to REQ-054 | `spec/requirements.md` | H05 | Medium |
| Add Data Format Contracts section | `docs/design-v1.2.md` §3 | C04, C05 | High |
| Clarify consensus denominator scope | `docs/design-v1.2.md` §4 | H03 | High |

---

## Resolution — 2026-06-26

All 6 gate improvements applied to `CLAUDE.md` (project-local fix, not upstreamed to dev-workflow repo yet):

| Gap | Applied to CLAUDE.md | Gate affected |
|-----|---------------------|---------------|
| Cross-slice boundary check | Yes — added to Assumption Validation (a) | Phase 3.5 |
| Downstream-impact tracing | Yes — "trace at least 3 downstream consequences" | Phase 3.5 |
| Production-path step | Yes — "start app with production configuration" | Phase 5 Verify |
| Flow tracing in adversarial review | Yes — "trace user flows step-by-step first" | Phase 5 Verify |
| Flag spec ambiguities | Yes — "flag in plan document and escalate" | Phase 3 Plan |
| Visual fidelity check | Yes — "load page with representative data" | Phase 5 Verify |

Spec/doc changes also applied: REQ-022 tightened, REQ-082 clarified, REQ-123 added, REQ-054 updated for vertical filtering, Data Format Contracts §3 added to design doc.

The `workflow-skill/SKILL.md` changes (for the portable dev-workflow repo) remain pending — only the project-local CLAUDE.md was updated.
