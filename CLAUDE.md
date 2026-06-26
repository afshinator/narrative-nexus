# Narrative Nexus — Agent Startup

## Cold-start protocol

1. Read `/vault/Context/narrative-nexus.md` — recent history, session status, project knowledge pointer
2. Read `/vault/Knowledge/narrative-nexus.md` — durable reference: architecture, conventions, design decisions, gotchas
3. Cross-check key facts against actual project files (`package.json`, `git log --oneline -5`, `git status --short`)
4. Before creating a new plan slice: read `docs/deferred.md`
5. Project follows dev-workflow: Spec → Plan → Assumption Validation → Implement → Verify → Ship
6. Current slice status: 5 slices implemented (router, settings+panel, docker+db, onboarding, sources). Slice 5 (Source Profile) plan approved, pending implementation. 6 pages still stub.
