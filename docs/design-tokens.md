# Narrative Nexus — Design Tokens

Extracted from `docs/mocks/sources-dark.html` via `designlang`. Authority for all visual decisions. The mock IS the spec.

## Fonts

| Role | Family | Source | Weights |
|------|--------|--------|---------|
| Headings | Space Grotesk | Google Fonts | 400, 500, 600, 700 |
| Body | IBM Plex Sans | Google Fonts | 400, 500, 600 |
| Mono / Data | IBM Plex Mono | Google Fonts | 400, 500 |

Use dark-mode fonts for both light and dark modes.

## Colors — Light Mode (`:root`)

```css
--bg:        #eef0eb;
--nav-bg:    #e0e4da;
--surface:   #f7f8f5;
--surface2:  #e8ebe3;
--border:    #d0d5c7;
--text:      #1c2018;
--text-dim:  #606b5f;

/* Archetype colors — earthy, muted */
--navy:      #2e4a7c;
--navy-dim:  rgba(46,74,124,.10);
--red:       #8b2c28;
--red-dim:   rgba(139,44,40,.10);
--teal:      #276b52;
--teal-dim:  rgba(39,107,82,.10);
--slate:     #556453;
--slate-dim: rgba(85,100,83,.10);
--amber:     #7a5217;
--ink:       #2e4a7c;
```

## Colors — Dark Mode (`.dark`)

```css
--bg:        #0c0f0b;
--nav-bg:    #141810;
--surface:   #161a12;
--surface2:  #1f2619;
--border:    #2c3625;
--text:      #d2e4c5;
--text-dim:  #858f7b;

/* Archetype colors */
--navy:      #7eb3e0;    /* Early Breaker */
--navy-dim:  rgba(126,179,224,.13);
--red:       #d97878;    /* Unmatched Breaker */
--red-dim:   rgba(217,120,120,.13);
--teal:      #5ebd8e;    /* Late but Reliable */
--teal-dim:  rgba(94,189,142,.13);
--slate:     #90a882;    /* Consensus Echo */
--slate-dim: rgba(144,168,130,.13);
--amber:     #c49a42;    /* Warning / flags */
--ink:       #7eb3e0;    /* Same as navy, for interactive elements */
```

## Typography Scale

| Element | Font | Size | Weight | Line Height | Notes |
|---------|------|------|--------|-------------|-------|
| h1 | Space Grotesk | 32px (2rem) | 700 | 1 | Letter-spacing: -0.02em |
| h2 | Space Grotesk | 18.4px (1.15rem) | 700 | 1.55 | |
| Body | IBM Plex Sans | 16px (1rem) | 400 | 1.55 | |
| Nav links | IBM Plex Sans | 13.44px (0.84rem) | 400-600 | 1.55 | |
| Mono / Data | IBM Plex Mono | 11-14px | 400-500 | varies | Tabular nums |
| Footer | IBM Plex Mono | 12px (0.75rem) | 400 | 1.55 | Letter-spacing: 0.04em |

## Nav Bar

- Background: `var(--nav-bg)` (#141810)
- Height: 52px, sticky top, z-index 100
- Border-bottom: 1px solid `var(--border)`
- Brand: Space Grotesk 700, with SVG circle icon (20x20)
- Active link: `var(--navy)` color + bottom border 2px `var(--navy)`, weight 600
- Inactive link: `var(--text-dim)`, underline on hover
- Stub links: 50% opacity

## Spacing

Base unit: 4px. Page max-width: 1340px. Page padding: 32px.

## Border Radii

- Small (inputs, table rows): 4px
- Medium (cards): 12px  
- Pills / badges: 999px (fully rounded)

## Transitions

Default: 0.15s. Color + border-color transitions on interactive elements.

## Component Patterns

**Badges:** Fully rounded (999px), 4px 12px padding, 0.66rem, weight 600. Background at 10% opacity of archetype color, text at 100%.

**Cards:** Background `var(--surface)`, border 1px `var(--border)`, radius 12-14px, padding 20-24px.

**Links (nav):** No underline by default. Active state: border-bottom 2px solid archetype color + weight 600.

**Footer:** IBM Plex Mono, 0.75rem, `var(--text-dim)`, centered, letter-spacing 0.04em.

## Design Laws (UX18 — human, standing)

1. **Don't make the user think.** Explicit beats elegant.
2. **FONT FLOOR:** No rendered text below 12px (0.75rem) app-wide. Sole exception: chart-internal SVG/canvas labels where geometry forces it.
3. **CONTRAST FLOOR:** All text meets WCAG AA — 4.5:1 against its actual background. Applies in BOTH themes.
