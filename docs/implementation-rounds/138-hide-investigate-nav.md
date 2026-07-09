# Results — Hide Investigate from nav

**Date:** 2026-07-09
**Order:** Remove Investigate nav link only — keep page, route, component intact.
**Fingerprint:** 378 / 10 / 358 / 17 / 13653 (unchanged both ends)

---

## 1. ECHO

Hide Investigate from top nav. Remove link only — do not delete page, route, or component. `/investigate` must still resolve if typed directly.

---

## 2. Evidence

### 2a. Target confirmed

```
$ grep -rl "Investigate" src/components/
src/components/AppNav.tsx

$ grep -n "nvestigate" src/components/AppNav.tsx
10:     { to: "/investigate", label: "Investigate" },
```

### 2b. Diff (one line removed)

```
$ git diff -- src/components/AppNav.tsx
diff --git a/src/components/AppNav.tsx b/src/components/AppNav.tsx
index 82c09ce..fda0199 100644
--- a/src/components/AppNav.tsx
+++ b/src/components/AppNav.tsx
@@ -7,7 +7,6 @@ import { OnboardingDialog } from "./OnboardingDialog";
 const navItems = [
        { to: "/", label: "Sources" },
        { to: "/pipeline", label: "Pipeline" },
-       { to: "/investigate", label: "Investigate" },
        { to: "/panel", label: "Panel" },
 ] as const;
```

### 2c. Route still registered

```
$ grep -rn "investigate" src/ --include=*.tsx -i | grep -i route
src/App.tsx:36:   <Route path="investigate" element={<InvestigatePage />} />
```

### 2d. Build passes

```
$ npm run build
...
✓ built in 445ms
```

708 modules transformed. Investigate chunk (`Investigate-BTKuLcXd.js`, 27.83 kB) still present in dist/ — component not tree-shaken.

### 2e. Fingerprint (both ends)

Before: `378 / 10 / 358 / 17 / 13653`
After:  `378 / 10 / 358 / 17 / 13653`

---

## 3. PROPOSED (not done)

None.

---

## 4. Compliance Table

| # | Requirement | Met EXACTLY? | Evidence |
|---|-------------|--------------|----------|
| 1 | Remove Investigate nav link only | YES | `git diff` shows single line deletion from navItems array |
| 2 | Do NOT delete the page component | YES | `dist/assets/Investigate-BTKuLcXd.js` still in build output |
| 3 | Do NOT delete the route | YES | `src/App.tsx:36` — `<Route path="investigate" ...>` intact |
| 4 | `/investigate` still resolves if typed directly | YES | Route registered, component bundled — SPA fallback handles deep link |
| 5 | No other nav items affected | YES | Sources, Pipeline, Panel, Stories, Settings all unchanged |
| 6 | Build passes | YES | `npm run build` — 445ms, zero errors |
| 7 | Fingerprint unchanged | YES | 378/10/358/17/13653 before and after |
