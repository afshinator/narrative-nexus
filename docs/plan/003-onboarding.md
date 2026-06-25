# Plan: Slice 3 — Onboarding Dialog

## Requirements addressed

| Req | Description | How |
|-----|-------------|-----|
| REQ-093 | 5-step walkthrough stored in localStorage via onboardingComplete | `OnboardingDialog.tsx` |
| REQ-094 | Re-accessible from ? icon in nav bar | onClick on AppNav's HelpCircle button |
| REQ-095 | Define all 5 vocabulary terms | 5 steps, one term per step |

## Design (from CONTEXT.md, updated)

- shadcn Dialog component
- 5 steps: Consensus Reality, Consensus-Absorbed, Cross-Source Convergent, Self-Consistent, Unresolved
- Auto-opens on mount when `onboardingComplete === false`
- Last step has **"Don't show again" checkbox**
  - Checked → `setOnboardingComplete(true)`, never auto-shows again
  - Unchecked → stays `false`, auto-shows next visit
- `?` icon opens dialog regardless of `onboardingComplete` state
- Dismissible (click outside or X to close)

## Vocabulary terms (from docs/design-v1.2.md §1)

| Step | Term | Definition |
|------|------|------------|
| 1 | Consensus Reality | The version of events agreed upon by the majority of the panel at a given threshold. Not "the truth." |
| 2 | Consensus-Absorbed | A claim that has entered the consensus version of events. Terminal state. |
| 3 | Cross-Source Convergent | A consensus-absorbed claim that was independently corroborated by another source before absorption. |
| 4 | Self-Consistent | A consensus-absorbed claim where only the origin source published consistent follow-up; no independent corroboration, but the panel eventually agreed. |
| 5 | Unresolved | A claim that never became consensus-absorbed after 90 days. Terminal state. |

## Architecture

Single component. No new routes. No store changes.

```
OnboardingDialog
  ├── open: auto on mount (if !onboardingComplete) or via ? icon
  ├── step 1-4: term + definition + "Next" button
  ├── step 5: term + definition + checkbox + "Finish" button
  └── dismiss: closes dialog (checkbox state determines store write)
```

Dialog open state managed locally (`useState`). The `?` icon in AppNav calls a function to open it — simplest approach: lift dialog state or use an event.

Ponytail approach: keep dialog state inside OnboardingDialog. Expose `open()` via `useImperativeHandle` + `forwardRef`, or simpler: use a module-level event emitter. Simplest: just render OnboardingDialog inside AppNav and use a local state toggle.

**Decision:** Render `<OnboardingDialog />` inside AppNav. Use local `useState` for dialog open. The `?` button toggles open. On mount, if `!onboardingComplete`, auto-set open to true.

## Files to create

| File | Content |
|------|---------|
| `src/components/OnboardingDialog.tsx` | 5-step dialog with forward/back, checkbox, vocabulary terms |

## Files to modify

| File | Change |
|------|--------|
| `src/components/AppNav.tsx` | Import OnboardingDialog, render it, add onClick to ? button |

## Verification

1. `npm run build` exits 0
2. `npm run test` — all 72 existing tests pass + new onboarding tests
3. Dialog auto-opens on first render (onboardingComplete is false)
4. "Don't show again" checked → sets onboardingComplete to true, dialog stays closed on re-render
5. "Don't show again" unchecked → onboardingComplete stays false, dialog re-opens
6. `?` icon opens dialog regardless of onboardingComplete state
7. All 5 vocabulary terms are displayed
