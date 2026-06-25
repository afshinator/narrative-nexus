# Design Language: Narrative Nexus — Sources (dark)

> Extracted from `http://localhost:3010/sources-dark.html` on June 24, 2026
> 558 elements analyzed

This document describes the complete design language of the website. It is structured for AI/LLM consumption — use it to faithfully recreate the visual design in any framework.

## Color Palette

### Primary Colors

| Role | Hex | RGB | HSL | Usage Count |
|------|-----|-----|-----|-------------|
| Primary | `#7eb3e0` | rgb(126, 179, 224) | hsl(208, 61%, 69%) | 29 |
| Secondary | `#d97878` | rgb(217, 120, 120) | hsl(0, 56%, 66%) | 30 |
| Accent | `#c49a42` | rgb(196, 154, 66) | hsl(41, 52%, 51%) | 16 |

### Neutral Colors

| Hex | HSL | Usage Count |
|-----|-----|-------------|
| `#738567` | hsl(96, 13%, 46%) | 164 |
| `#1f2619` | hsl(92, 21%, 12%) | 37 |
| `#90a882` | hsl(98, 18%, 58%) | 20 |
| `#000000` | hsl(0, 0%, 0%) | 18 |
| `#2c3625` | hsl(95, 19%, 18%) | 10 |
| `#161a12` | hsl(90, 18%, 9%) | 6 |
| `#0c0f0b` | hsl(105, 15%, 5%) | 2 |

### Background Colors

Used on large-area elements: `#0c0f0b`, `#141810`, `#2c3625`, `#161a12`

### Text Colors

Text color palette: `#000000`, `#d2e4c5`, `#7eb3e0`, `#738567`, `#d97878`, `#c49a42`, `#5ebd8e`, `#90a882`

### Full Color Inventory

| Hex | Contexts | Count |
|-----|----------|-------|
| `#d2e4c5` | text, border | 878 |
| `#738567` | text, border, background | 164 |
| `#5ebd8e` | text, border, background | 48 |
| `#1f2619` | background | 37 |
| `#d97878` | text, border, background | 30 |
| `#7eb3e0` | text, border, background | 29 |
| `#90a882` | text, background, border | 20 |
| `#000000` | text, border | 18 |
| `#c49a42` | text, border, background | 16 |
| `#2c3625` | background, border | 10 |
| `#161a12` | background | 6 |
| `#0c0f0b` | background | 2 |

## Typography

### Font Families

- **IBM Plex Sans** — used for body (480 elements)
- **IBM Plex Mono** — used for body (57 elements)
- **Space Grotesk** — used for all (12 elements)
- **Times New Roman** — used for body (9 elements)

### Type Scale

| Size (px) | Size (rem) | Weight | Line Height | Letter Spacing | Used On |
|-----------|------------|--------|-------------|----------------|---------|
| 32px | 2rem | 700 | 32px | -0.64px | h1, div |
| 18.4px | 1.15rem | 700 | 28.52px | normal | h2 |
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
| 10.4px | 0.65rem | 400 | 16.12px | 0.832px | span |

### Heading Scale

```css
h1 { font-size: 32px; font-weight: 700; line-height: 32px; }
h2 { font-size: 18.4px; font-weight: 700; line-height: 28.52px; }
```

### Body Text

```css
body { font-size: 11.264px; font-weight: 400; line-height: 17.4592px; }
```

### Font Weights in Use

`400` (440x), `600` (81x), `700` (20x), `500` (17x)

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
--bg: #0c0f0b;
--nav-bg: #141810;
--border: #2c3625;
```

### Typography

```css
--text: #d2e4c5;
--text-dim: #738567;
```

### Other

```css
--scale: 1;
--fs-base: calc(1rem * var(--scale));
--surface: #161a12;
--surface2: #1f2619;
--navy: #7eb3e0;
--navy-dim: rgba(126,179,224,.13);
--red: #d97878;
--red-dim: rgba(217,120,120,.13);
--teal: #5ebd8e;
--teal-dim: rgba(94,189,142,.13);
--slate: #90a882;
--slate-dim: rgba(144,168,130,.13);
--amber: #c49a42;
--ink: #7eb3e0;
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
  color: rgb(115, 133, 103);
  font-size: 13.44px;
  font-weight: 400;
}
```

### Navigation (3 instances)

```css
.navigatio {
  background-color: rgb(20, 24, 16);
  color: rgb(210, 228, 197);
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
  color: rgb(115, 133, 103);
  padding-top: 0px;
  padding-bottom: 0px;
  font-size: 11.2px;
}
```

### Tables (1 instances)

```css
.table {
  border-color: rgb(210, 228, 197);
  cell-style: [object Object];
}
```

### Badges (20 instances)

```css
.badge {
  background-color: rgba(94, 189, 142, 0.1);
  color: rgb(94, 189, 142);
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
| `#d2e4c5` | `#1f2619` | 11.59:1 | AAA |

## Dark Mode

The site has a distinct dark mode color scheme:

- **Primary:** `#7eb3e0`
- **Secondary:** `#d97878`
- **Backgrounds:** `#0c0f0b`, `#141810`, `#2c3625`, `#161a12`
- **Text:** `#000000`, `#d2e4c5`, `#7eb3e0`, `#738567`, `#d97878`

### Dark Mode CSS Variables

```css
--bg: #0c0f0b;
--nav-bg: #141810;
--border: #2c3625;
--text: #d2e4c5;
--text-dim: #738567;
--scale: 1;
--fs-base: calc(1rem * var(--scale));
--surface: #161a12;
--surface2: #1f2619;
--navy: #7eb3e0;
--navy-dim: rgba(126,179,224,.13);
--red: #d97878;
--red-dim: rgba(217,120,120,.13);
--teal: #5ebd8e;
--teal-dim: rgba(94,189,142,.13);
--slate: #90a882;
--slate-dim: rgba(144,168,130,.13);
--amber: #c49a42;
--ink: #7eb3e0;
--fs-base: --scale;
success: [object Object];
warning: [object Object];
error: [object Object];
info: [object Object];
```

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
- 4 font families — consider limiting to 2 (heading + body)
- 72% of CSS is unused — consider purging
- 340 duplicate CSS declarations

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

**Icon colors:** `var(--navy)`, `rgb(0, 0, 0)`, `var(--red)`, `var(--teal)`, `var(--slate)`, `#738567`, `#7eb3e0`, `var(--border)`, `#5ebd8e`, `#90a882`

## Font Files

| Family | Source | Weights | Styles |
|--------|--------|---------|--------|
| IBM Plex Mono | google-fonts | 400, 500 | normal |
| IBM Plex Sans | google-fonts | 400, 500, 600 | normal |
| Space Grotesk | google-fonts | 400, 500, 600, 700 | normal |

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
| Avg saturation | 0.322 |
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
