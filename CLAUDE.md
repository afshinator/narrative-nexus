# Narrative Nexus — Agent Startup

## Cold-start protocol

1. Read `/vault/Context/narrative-nexus.md` — recent history, session status, project knowledge pointer
2. Read `/vault/Knowledge/narrative-nexus.md` — durable reference: architecture, conventions, design decisions, gotchas
3. Cross-check key facts against actual project files (`package.json`, `git log --oneline -5`, `git status --short`)
4. Before creating a new plan slice: read `docs/deferred.md`
5. Project follows dev-workflow gates in strict order. Each gate must be explicitly completed before the next begins:

   **Spec → Plan → Assumption Validation → Implement (TDD) → Verify**

   - **Spec:** requirements doc, tagged REQs. Already done for this project.
   - **Plan:** write a plan slice document with deps, assumptions, architecture decisions, implementation order, test strategy, verification checklist. When a spec requirement is ambiguous, flag the ambiguity in the plan document and escalate for clarification — do not silently choose an interpretation. If the interpretation is resolved, update the spec to remove the ambiguity.
   - **Assumption Validation:** TWO parts — (a) verify every dependency and claim in the plan against the actual codebase/environment (fact-checking). For slices that produce or consume data crossing a slice boundary, also validate cross-slice data format contracts: date/time format, URL format, null/value encoding, number scale. For every external dependency tradeoff documented in the plan, trace at least 3 downstream consequences before proceeding. (b) run `grill-with-docs` to stress-test decisions against domain terminology, ADRs, design doc. Do NOT skip to implementation after part (a). Offer both parts before proceeding.
   - **Implement (TDD):** load ponytail first (full intensity). Red-green-refactor: write failing tests first, then make them pass. Prefer stdlib, fewest files, shortest working diff. No unrequested abstractions. Mark deliberate shortcuts with `# ponytail:` comments.
   - **Verify:** before running the full test suite, start the application with production configuration (persistent SQLite file, real env vars) and verify at least one primary user flow end-to-end. Then sanity-check the implementation (does the thing actually work as intended?). For adversarial review: trace primary user flows step-by-step first, then read source code to verify each step is actually implemented — never start by reading files. Run adversarial review for algorithmic code (scraping, consensus math, claim lifecycle, agents — per vault Knowledge), skip for plumbing/UI binding. Run `ponytail-review` against the diff. For visual changes: load the page with representative data and confirm colors match dimension polarity, chart scales are consistent, and empty states look intentional. Then run `npm run build`, `vitest run`, `biome check src/`, `pytest`. Confirm no regressions. Provide a commit message (user handles the actual commit/push). If all clean, proceed to Plan for the next slice.

6. Current slice status: 7 frontend slices + 8a backend scaffold + 8b scraper/scheduler + 8c consensus engine + 9 scraper controls/header status + 10 agent3 hardening/snapshots/pipeline orchestration + 11 regional source expansion + 12 provider abstraction layer + Agents 1/2/4 completed. All 4 agents execute against real providers (OpenCode Zen for LLM, local sentence-transformers for embeddings). Pipeline runner wired to runtime provider overrides. Pipeline Flow page has per-stage provider dropdowns + AMD shortcut. Next: demo seed script + visual polish OR deferred items (timeline markers, Vf trend, outlier waterfall, silent edit log, tier radar — all now unblocked).

7. Before creating a new plan slice: read `docs/deferred.md`. After gated plan approval, update CLAUDE.md line 6.
