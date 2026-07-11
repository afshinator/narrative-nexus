# Gemma Status — Open Items Confirmed

**Date:** 2026-07-11

---

## Label Cleanup — Confirmed Clean

AMD badge (red `FIREWORKS API` pill at `PipelineFlow.tsx:489`) is independent of dropdown label text. README line 57 accurate. Fallback format `{name} (AMD) — {model}` preserved for non-labeled entries.

## Two Open Items (unchanged)

1. **Slug in committed file:** `accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx` in `config/providers.json`. UI-hidden, not repo-hidden.
2. **Deployment status unknown:** STATUS.md says "deployment deleted." Selecting Gemma + running pipeline = crash.

## Recommendation

Remove `fireworks-gemma` from the functional provider list. Keep `docs/evidence/gemma/` intact. One deletion fixes both the committed slug and the crash risk.

Neither blocks submission if Gemma is simply not selected live.
