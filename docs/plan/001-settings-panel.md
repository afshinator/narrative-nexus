# Plan: Slice 1 — Settings + Panel Management Pages

## Requirements addressed

| Req | Description | How |
|-----|-------------|-----|
| REQ-091 | Panel Management — activate/deactivate sources, category balance indicator | `PanelPage.tsx` |
| REQ-092 | Settings — consensus thresholds, font scale slider, theme selector | `SettingsPage.tsx` |
| REQ-024 | Default thresholds: GEOPOLITICS 65%, ECONOMICS 75%, TECHNOLOGY 75% | `src/data/thresholds.ts` (single source of truth) |
| REQ-025 | Thresholds configurable at runtime | zustand store, persisted to localStorage |
| REQ-048–053 | 20 default sources across 5 tiers | `src/data/sources.ts` (single source of truth) |

## Design guidance (from docs/design-v1.2.md §6)

- Dark terminal / forensic intelligence console aesthetic
- Use existing `--nn-*` CSS custom properties — no new colors
- Monospace (`font-mono`) for data values, thresholds, tier labels
- Geist sans-serif for UI labels, prose
- shadcn components for interactive controls

## Separation of concerns

- **`src/data/thresholds.ts`** — single source of truth for default consensus thresholds. Export `DEFAULT_THRESHOLDS` and `Thresholds` type. Store reads from this, Settings UI writes to store. Modify one file to change defaults.
- **`src/data/sources.ts`** — single source of truth for 20 default sources with tier, name, domain. Export `DEFAULT_SOURCES` and `Source` type. Store tracks active/inactive state as `Set<sourceId>`. Panel UI reads from store.

## Store changes (`src/store.ts`)

Add to `StoreState`:
- `consensusThresholds: { geopolitics: number; economics: number; technology: number }` — initialized from `DEFAULT_THRESHOLDS`
- `activeSources: string[]` — array of active source domain slugs (persisted)
- `setConsensusThreshold(vertical, value)` — update one threshold
- `toggleSource(slug)` — add/remove from activeSources
- `resetThresholds()` — restore defaults from `DEFAULT_THRESHOLDS`

## Settings page (`src/pages/Settings.tsx`)

Three sections, each with a shadcn Card:
1. **Consensus Thresholds** — 3 sliders (65/75/75), monospace labels, reset button
2. **Font Scale** — slider 0.8–1.5, live preview, persisted (already in store)
3. **Theme** — dark/light toggle (already in store, CSS already applied)

## Panel Management page (`src/pages/Panel.tsx`)

Two sections:
1. **Category balance indicator** — bar showing tier distribution (Tier1: 5, Tier2: 5, Tier3: 5, Tier4: 3, Tier5: 2... and if deactivated, show "N active" vs "N total")
2. **Source list** — grouped by tier, each source has name + domain + active/inactive toggle (shadcn Switch)

## Font scale CSS

Add to `src/index.css`:
```css
:root { --font-scale: 1; }
html { font-size: calc(1rem * var(--font-scale)); }
```
Store subscription in `main.tsx` updates `document.documentElement.style.setProperty('--font-scale', fontScale)`.

## Assumptions validated (Phase 3.5)

1. **shadcn Switch, Slider, Card** — `npx shadcn add switch slider card` creates files but places them in `@/components/ui/` instead of `src/components/ui/`. **Fix applied:** moved to `src/components/ui/`. Build exits 0, all imports resolve.

   ⚠ **Recurring workflow step:** every `npx shadcn add <component>` produces files in `@/` — must be moved to `src/` and the empty `@/` directory removed. This is a shadcn CLI quirk with our alias config.

## Files to create

| File | Content |
|------|---------|
| `src/data/thresholds.ts` | `Thresholds` type + `DEFAULT_THRESHOLDS` constant |
| `src/data/sources.ts` | `Source` type + `DEFAULT_SOURCES` array (20 entries) |

## Files to modify

| File | Change |
|------|--------|
| `src/store.ts` | Add consensusThresholds + activeSources + setters |
| `src/pages/Settings.tsx` | Replace stub with full page |
| `src/pages/Panel.tsx` | Replace stub with full page |
| `src/index.css` | Add `--font-scale` custom property |
| `src/main.tsx` | Subscribe to fontScale → CSS custom property |

## Verification

1. `npm run build` exits 0
2. `npm run test` — all tests pass (existing 13 + new Settings/Panel tests)
3. Settings page: 3 threshold sliders, font scale slider, theme toggle — all persist on reload
4. Panel page: 20 sources listed by tier, toggles persist, category balance updates
5. Font scale changes text size across the whole app
6. No new CSS colors — all styling uses existing `--nn-*` tokens
