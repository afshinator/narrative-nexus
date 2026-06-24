# ui-design
See [ui-design/taste.md](ui-design/taste.md)

# navigation
- Drill-down/detail pages should not be top-level navigation items; only accessible via click-through from parent views (e.g., source profile → cluster, timeline → article). Confidence: 0.70

# project-boundaries
- Treat differently-named projects as distinct even when their files coexist in the same directory tree (e.g., design docs/mocks in `docs/` of another repo are a separate project, not part of the containing repo). Confidence: 0.90
- When saving information to a project knowledge file, append new information rather than overwriting existing content. Confidence: 0.80

# analysis-accuracy
- Be precise about which design tokens/patterns actually exist in the code vs extrapolated — verify across all pages before making assertions. Confidence: 0.70

# dev-workflow
- Follow the dev-workflow development methodology: Spec (tagged requirements) → Plan (vertical slices with deps/assumptions) → Assumption Validation (PoC before building) → Implement (TDD per slice) → Verify (spec-coverage + tests + adversarial review) → Ship (CI + human review). Do not skip verification/validation steps in favor of "just build" — user explicitly rejects building without a trusted, verified workflow. Confidence: 0.85
- Keep plan slices small and focused — plan one endpoint/page at a time rather than trying to plan all components simultaneously. Overambitious planning that tries to solve everything at once will be rejected. Confidence: 0.75
- When UX/design questions arise during planning, present clear recommendations with rationale rather than punting open-ended design decisions to the user. Only escalate genuinely incomparable alternatives where the assistant cannot meaningfully choose. Confidence: 0.80

# docs
- UX briefs and design docs should describe only the current design state — omit version history, 'previously' language, and references to discarded/earlier designs. Define base functionality, not specific decoration-level items (colors, fonts, etc.) that are easy to change. Confidence: 0.85
- When extracting requirements from an original spec, keep derivative documents tightly coupled to the original's narrative structure. The user needs to see continuity between spec and requirements to make informed design decisions — a bare-bullet requirements doc that loses the "why" creates a disconnect that blocks progress. Confidence: 0.70

# architecture
- Isolate configuration values (scatter shapes, timeline visuals, pipeline replay behavior, etc.) into dedicated constants files or functions so they can be easily modified without touching core logic. Always follow separation of concerns. Confidence: 0.90
