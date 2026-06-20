# ui-design
See [ui-design/taste.md](ui-design/taste.md)
# ui-design
See [ui-design/taste.md](ui-design/taste.md)
# navigation
- Drill-down/detail pages should not be top-level navigation items; only accessible via click-through from parent views (e.g., source profile → cluster, timeline → article). Confidence: 0.70

# project-boundaries
- Treat differently-named projects as distinct even when their files coexist in the same directory tree (e.g., design docs/mocks in `docs/` of another repo are a separate project, not part of the containing repo). Confidence: 0.90
- When saving information to a project knowledge file, append new information rather than overwriting existing content. Confidence: 0.80

# analysis-accuracy
- Be precise about which design tokens/patterns actually exist in the code vs extrapolated — verify across all pages before making assertions. Confidence: 0.70

# docs
- UX briefs and design docs should describe only the current design state — omit version history, 'previously' language, and references to discarded/earlier designs. Define base functionality, not specific decoration-level items (colors, fonts, etc.) that are easy to change. Confidence: 0.85
