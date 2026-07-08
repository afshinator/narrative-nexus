# UX28-FIX — Scraper Button Must Be Visibly Disabled

**Round:** UX28-FIX
**Date:** 2026-07-08
**Type:** Button state fix. NO DB writes.

---

## Q1 — Diagnosis + Fix

**Current state:** `PipelineFlow.tsx:257` — `disabled={pending || status === null}`. Does NOT check `status.readonly`. Button renders as live Play in readonly mode, onClick fires POST → silently 403s.

**Fix:** `PipelineFlow.tsx:257,262-266`:

```diff
- disabled={pending || status === null}
+ disabled={pending || status === null || status?.readonly}

- className={`... ${status?.running ? "red" : "teal"}`}
+ className={`... disabled:cursor-not-allowed ... ${
+   status?.readonly ? "border bg-surface text-dim"
+   : status?.running ? "red" : "teal"
+ }`}

- {status?.running ? <Square/> Stop : <Play/> Start}
+ {status?.readonly ? <>Scraper (paused)</>
+  : status?.running ? <Square/> Stop : <Play/> Start}
```

Changes:
1. `disabled` attribute set when readonly → no 403 round-trip
2. Visually muted: `border-[var(--nn-border)] bg-[var(--nn-surface)] text-[var(--nn-text-dim)]` — gray/neutral, not teal or red
3. `disabled:cursor-not-allowed` added
4. Button text: "Scraper (paused)" — two words, no icon, no long sentence

---

## Q2 — Non-Readonly Path Unchanged

When `status?.readonly` is falsy/undefined (no `.readonly` sentinel, or status endpoint doesn't return the field):

- `disabled={pending || status === null}` — same as before
- Button renders teal "Start" or red "Stop" with Play/Square icons
- onClick fires `toggle("start"/"stop")` → POST to backend
- NO change to the live path

Verified via code logic only — did NOT start scraper against demo.db.

---

## Q3 — Final Rendered States

### READONLY MODE (sentinel present, `status.readonly === true`)

```
┌─────────────────────────────────────┐
│  [ Scraper (paused) ]  Paused · 0   │
│   gray border, dim text, not-allowed │
│   cursor, HTML disabled              │
└─────────────────────────────────────┘
```

- Button: gray border, surface bg, dim text, `cursor: not-allowed`
- Label: "Scraper (paused)" — no icon
- Status span: "Paused" (from status endpoint)
- Click does NOTHING — `disabled` attribute blocks event

### NORMAL MODE (no sentinel, `status.readonly` falsy)

```
┌─────────────────────────────────────┐
│  [ ▶ Start ]  Paused                │
│   teal bg, white text, pointer       │
│   cursor, HTML enabled               │
└─────────────────────────────────────┘
```

- Button: teal bg, white text, Play icon, `cursor: pointer`
- Status span: "Paused"
- Click fires `POST /api/scraper/start`

---

## Compliance Table

| Requirement | Met? | Evidence |
|---|---|---|
| ROUND OBJECTIVE — Readonly: disabled + label, no request; normal: unchanged | YES | Code diff |
| Q1 — Disabled when readonly | YES | `disabled={... || status?.readonly}` |
| Q1 — Visually muted | YES | Gray border/surface/dim text + not-allowed cursor |
| Q1 — Short label | YES | "Scraper (paused)" — two words |
| Q2 — Normal path unchanged | YES | Ternary: readonly check first, else original logic |
| Q3 — Both states documented | YES | Rendered-state descriptions |
| DB untouched | YES | Zero writes |
| Build passes | YES | 646ms |
| Vitest baseline | YES | 12 failed/122 passed/4 skipped |

---

## Modified Files

- `src/pages/PipelineFlow.tsx` — lines 257, 262-266: readonly disabled state
