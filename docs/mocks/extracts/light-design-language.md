# Design Language: Narrative Nexus — Sources

> Extracted from `http://localhost:3011/sources.html` on June 24, 2026
> 558 elements analyzed

This document describes the complete design language of the website. It is structured for AI/LLM consumption — use it to faithfully recreate the visual design in any framework.

## Color Palette

### Primary Colors

| Role | Hex | RGB | HSL | Usage Count |
|------|-----|-----|-----|-------------|
| Primary | `#7a5217` | rgb(122, 82, 23) | hsl(36, 68%, 28%) | 16 |
| Secondary | `#276b52` | rgb(39, 107, 82) | hsl(158, 47%, 29%) | 48 |
| Accent | `#8b2c28` | rgb(139, 44, 40) | hsl(2, 55%, 35%) | 30 |

### Neutral Colors

| Hex | HSL | Usage Count |
|-----|-----|-------------|
| `#1c2018` | hsl(90, 14%, 11%) | 878 |
| `#717a68` | hsl(90, 8%, 44%) | 164 |
| `#e8ebe3` | hsl(82, 17%, 91%) | 38 |
| `#5c6b5a` | hsl(113, 9%, 39%) | 20 |
| `#000000` | hsl(0, 0%, 0%) | 18 |
| `#d0d5c7` | hsl(81, 14%, 81%) | 10 |
| `#f7f8f5` | hsl(80, 18%, 97%) | 6 |
| `#e0e4da` | hsl(84, 16%, 87%) | 1 |

### Background Colors

Used on large-area elements: `#eef0eb`, `#e0e4da`, `#d0d5c7`, `#f7f8f5`

### Text Colors

Text color palette: `#000000`, `#1c2018`, `#2e4a7c`, `#717a68`, `#8b2c28`, `#7a5217`, `#276b52`, `#5c6b5a`

### Full Color Inventory

| Hex | Contexts | Count |
|-----|----------|-------|
| `#1c2018` | text, border | 878 |
| `#717a68` | text, border, background | 164 |
| `#276b52` | text, border, background | 48 |
| `#e8ebe3` | background | 38 |
| `#8b2c28` | text, border, background | 30 |
| `#2e4a7c` | text, border, background | 29 |
| `#5c6b5a` | text, background, border | 20 |
| `#000000` | text, border | 18 |
| `#7a5217` | text, border, background | 16 |
| `#d0d5c7` | background, border | 10 |
| `#f7f8f5` | background | 6 |
| `#e0e4da` | background | 1 |

## Typography

### Font Families

- **IBM Plex Sans** — used for body (473 elements)
- **IBM Plex Mono** — used for body (57 elements)
- **Fraunces** — used for all (12 elements)
- **Times New Roman** — used for body (9 elements)
- **Newsreader** — used for body (7 elements)

### Type Scale

| Size (px) | Size (rem) | Weight | Line Height | Letter Spacing | Used On |
|-----------|------------|--------|-------------|----------------|---------|
| 32px | 2rem | 700 | 32px | -0.64px | h1, div |
| 19.2px | 1.2rem | 700 | 29.76px | normal | h2 |
| 16.8px | 1.05rem | 600 | 26.04px | -0.168px | span, svg, circle |
| 16px | 1rem | 400 | normal | normal | html, head, meta, title |
| 14.4px | 0.9rem | 400 | 22.32px | normal | p |
| 14.08px | 0.88rem | 400 | 21.824px | normal | table, thead, tr, tbody |
| 13.44px | 0.84rem | 600 | 20.832px | normal | a, span, svg, path |
| 13.12px | 0.82rem | 400 | 20.336px | normal | span |
| 12.8px | 0.8rem | 400 | 19.84px | normal | span, svg, circle, rect |
| 12.672px | 0.792rem | 600 | 19.6416px | normal | td, svg, circle, rect |
| 12.48px | 0.78rem | 400 | 19.344px | normal | div |
| 11.52px | 0.72rem | 600 | 17.856px | 0.576px | div |
| 11.264px | 0.704rem | 400 | 17.4592px | normal | span |
| 11.2px | 0.7rem | 700 | 17.36px | 0.672px | div, p |
| 10.56px | 0.66rem | 600 | 16.368px | 0.2112px | span |

### Heading Scale

```css
h1 { font-size: 32px; font-weight: 700; line-height: 32px; }
h2 { font-size: 19.2px; font-weight: 700; line-height: 29.76px; }
```

### Body Text

```css
body { font-size: 11.264px; font-weight: 400; line-height: 17.4592px; }
```

### Font Weights in Use

`400` (440x), `600` (86x), `500` (17x), `700` (15x)

## Spacing

**Base unit:** 4px

| Token | Value | Rem |
|-------|-------|-----|
| spacing-1 | 1px | 0.0625rem |
| spacing-32 | 32px | 2rem |
| spacing-36 | 36px | 2.25rem |
| spacing-64 | 64px | 4rem |

## Border Radii

| Label | Value | Count |
|-------|-------|-------|
| sm | 4px | 72 |
| lg | 12px | 1 |
| xl | 20px | 1 |
| full | 50px | 5 |
| full | 999px | 23 |

## CSS Custom Properties

### Colors

```css
--bg: #eef0eb;
--nav-bg: #e0e4da;
--border: #d0d5c7;
```

### Typography

```css
--text: #1c2018;
--text-dim: #717a68;
```

### Other

```css
--scale: 1;
--fs-base: calc(1rem * var(--scale));
--surface: #f7f8f5;
--surface2: #e8ebe3;
--navy: #2e4a7c;
--navy-dim: rgba(46,74,124,.10);
--red: #8b2c28;
--red-dim: rgba(139,44,40,.10);
--teal: #276b52;
--teal-dim: rgba(39,107,82,.10);
--slate: #5c6b5a;
--slate-dim: rgba(92,107,90,.10);
--amber: #7a5217;
--ink: #2e4a7c;
```

### Dependencies

```css
--fs-base: --scale;
```

### Semantic

```css
success: [object Object];
warning: [object Object];
error: [object Object];
info: [object Object];
```

## Transitions & Animations

**Durations:** `0.15s`, `0.35s`

### Common Transitions

```css
transition: all;
transition: color 0.15s, border-color 0.15s;
transition: 0.15s;
```

### Keyframe Animations

**blip**
```css
@keyframes blip {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.25; }
}
```

**rowIn**
```css
@keyframes rowIn {
  0% { opacity: 0; transform: translateY(3px); }
  100% { opacity: 1; transform: none; }
}
```

## Component Patterns

Detected UI component patterns and their most common styles:

### Links (8 instances)

```css
.link {
  color: rgb(113, 122, 104);
  font-size: 13.44px;
  font-weight: 400;
}
```

### Navigation (3 instances)

```css
.navigatio {
  background-color: rgb(224, 228, 218);
  color: rgb(28, 32, 24);
  padding-top: 0px;
  padding-bottom: 0px;
  padding-left: 0px;
  padding-right: 0px;
  position: static;
}
```

### Footer (1 instances)

```css
.foote {
  color: rgb(113, 122, 104);
  padding-top: 0px;
  padding-bottom: 0px;
  font-size: 11.2px;
}
```

### Tables (1 instances)

```css
.table {
  border-color: rgb(28, 32, 24);
  cell-style: [object Object];
}
```

### Badges (20 instances)

```css
.badge {
  background-color: rgba(39, 107, 82, 0.1);
  color: rgb(39, 107, 82);
  font-size: 10.56px;
  font-weight: 600;
  padding-top: 4px;
  padding-right: 12px;
  border-radius: 999px;
}
```

## Layout System

**3 grid containers** and **101 flex containers** detected.

### Container Widths

| Max Width | Padding |
|-----------|---------|
| 1340px | 32px |

### Grid Column Patterns

| Columns | Usage Count |
|---------|-------------|
| 4-column | 2x |
| 5-column | 1x |

### Grid Templates

```css
grid-template-columns: 302.75px 302.75px 302.75px 302.75px;
gap: 1px;
grid-template-columns: 285.5px 285.5px 285.5px 285.5px;
gap: 8px;
grid-template-columns: 226.797px 226.797px 226.797px 226.797px 226.812px;
gap: 8px;
```

### Flex Patterns

| Direction/Wrap | Count |
|----------------|-------|
| row/nowrap | 98x |
| row/wrap | 3x |

**Gap values:** `12px`, `1px`, `2px`, `5px`, `6px`, `7px`, `8px`, `9px`

## Accessibility (WCAG 2.1)

**Overall Score: 100%** — 1 passing, 0 failing color pairs

### Passing Color Pairs

| Foreground | Background | Ratio | Level |
|------------|------------|-------|-------|
| `#1c2018` | `#e8ebe3` | 13.73:1 | AAA |

## Design System Score

**Overall: 82/100 (Grade: B)**

| Category | Score |
|----------|-------|
| Color Discipline | 100/100 |
| Typography Consistency | 50/100 |
| Spacing System | 85/100 |
| Shadow Consistency | 85/100 |
| Border Radius Consistency | 90/100 |
| Accessibility | 100/100 |
| CSS Tokenization | 100/100 |

**Strengths:** Tight, disciplined color palette, Well-defined spacing scale, Clean elevation system, Consistent border radii, Strong accessibility compliance, Good CSS variable tokenization

**Issues:**
- 5 font families — consider limiting to 2 (heading + body)
- 76% of CSS is unused — consider purging
- 383 duplicate CSS declarations

## Z-Index Map

**1 unique z-index values** across 1 layers.

| Layer | Range | Elements |
|-------|-------|----------|
| dropdown | 100,100 | nav.a.p.p.n.a.v |

## SVG Icons

**42 unique SVG icons** detected. Dominant style: **outlined**.

| Size Class | Count |
|------------|-------|
| xs | 23 |
| md | 1 |
| lg | 18 |

**Icon colors:** `var(--navy)`, `rgb(0, 0, 0)`, `var(--red)`, `var(--teal)`, `var(--slate)`, `#717a68`, `#2e4a7c`, `var(--border)`, `#276b52`, `#5c6b5a`

## Font Files

| Family | Source | Weights | Styles |
|--------|--------|---------|--------|
| Fraunces | google-fonts | 600, 700, 900 | italic, normal |
| IBM Plex Mono | google-fonts | 400, 500 | normal |
| IBM Plex Sans | google-fonts | 400, 500, 600 | normal |
| Newsreader | google-fonts | 400, 500 | italic, normal |

**Google Fonts URL:** `https://fonts.googleapis.com/`

## Motion Language

**Feel:** mixed · **Scroll-linked:** yes

### Duration Tokens

| name | value | ms |
|---|---|---|
| `xs` | `150ms` | 150 |

### Keyframes In Use

| name | kind | properties | uses |
|---|---|---|---|
| `blip` | fade | opacity | 1 |
| `rowIn` | slide-y | opacity, transform | 18 |

## Page Intent

**Type:** `unknown` (confidence 0)

## Section Roles

Reading order (top→bottom): nav

| # | Role | Heading | Confidence |
|---|------|---------|------------|
| 0 | nav | — | 0.9 |

## Material Language

**Label:** `flat` (confidence 0)

| Metric | Value |
|--------|-------|
| Avg saturation | 0.292 |
| Shadow profile | none |
| Avg shadow blur | 0px |
| Max radius | 999px |
| backdrop-filter in use | no |
| Gradients | 0 |

## Quick Start

To recreate this design in a new project:

1. **Install fonts:** Add `IBM Plex Sans` from Google Fonts or your font provider
2. **Import CSS variables:** Copy `variables.css` into your project
3. **Tailwind users:** Use the generated `tailwind.config.js` to extend your theme
4. **Design tokens:** Import `design-tokens.json` for tooling integration
