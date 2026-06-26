# Narrative Nexus — Agent Startup

## Cold-start protocol

1. Read `/vault/Context/narrative-nexus.md` — recent history, session status, project knowledge pointer
2. Read `/vault/Knowledge/narrative-nexus.md` — durable reference: architecture, conventions, design decisions, gotchas
3. Cross-check key facts against actual project files (`package.json`, `git log --oneline -5`, `git status --short`)
4. Before creating a new plan slice: read `docs/deferred.md`
5. Project follows dev-workflow gates in strict order. Each gate must be explicitly completed before the next begins:

   **Spec → Plan → Assumption Validation → Implement (TDD) → Verify**

   - **Spec:** requirements doc, tagged REQs. Already done for this project.
   - **Plan:** write a plan slice document with deps, assumptions, architecture decisions, implementation order, test strategy, verification checklist.
   - **Assumption Validation:** TWO parts — (a) verify every dependency and claim in the plan against the actual codebase/environment (fact-checking), (b) run `grill-with-docs` to stress-test decisions against domain terminology, ADRs, design doc. Do NOT skip to implementation after part (a). Offer both parts before proceeding.
   - **Implement (TDD):** load ponytail first (full intensity). Red-green-refactor: write failing tests first, then make them pass. Prefer stdlib, fewest files, shortest working diff. No unrequested abstractions. Mark deliberate shortcuts with `# ponytail:` comments.
   - **Verify:** sanity-check the implementation end-to-end first (does the thing actually work as intended?). Run adversarial review for algorithmic code (scraping, consensus math, claim lifecycle, agents — per vault Knowledge), skip for plumbing/UI binding. Run `ponytail-review` against the diff. Then run `npm run build`, `vitest run`, `biome check src/`, `pytest`. Confirm no regressions. Provide a commit message (user handles the actual commit/push). If all clean, proceed to Plan for the next slice.

6. Current slice status: 7 frontend slices + 8a backend scaffold + 8b scraper/scheduler + 8c consensus engine implemented. Next: Plan for frontend deferred items or next backend slice.

7. Before creating a new plan slice: read `docs/deferred.md`. After gated plan approval, update CLAUDE.md line 6.
