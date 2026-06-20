# Narrative Probe — Design Tokens

Audited from `docs/mocks-v3/index.html`. Items under "Needs tokenization" are hardcoded values that appear in multiple places.

---

## Currently Tokenized (CSS Variables)

### Surface hierarchy
| Token | v3 Light | v3 Dark |
|-------|----------|---------|
| `--bg` | `#f5f3ee` | `#0c0b12` |
| `--surface` | `#ffffff` | `#14131d` |
| `--surface2` | `#ece8e0` | `#1e1c2e` |
| `--border` | `#d8d4cc` | `#2a2840` |

### Text
| Token | v3 Light | v3 Dark |
|-------|----------|---------|
| `--text` | `#1c1a16` | `#e6e4f0` |
| `--text-dim` | `#7a7568` | `#8a86a0` |

### Semantic / Signal
| Token | v3 Light | v3 Dark | Meaning |
|-------|----------|---------|---------|
| `--navy` | `#1e3a5f` | `#60a5fa` | accent, active states, badges |
| `--navy-dim` | `rgba(30,58,95,.08)` | `rgba(59,130,246,.12)` | hover tints |
| `--forest` | `#2d6a4f` | `#34d399` | positive scores, consensus |
| `--forest-dim` | `rgba(45,106,79,.1)` | `rgba(52,211,153,.1)` | positive bg |
| `--amber` | `#b8860b` | `#fbbf24` | warning, moderate scores |
| `--amber-dim` | `rgba(184,134,11,.1)` | `rgba(251,191,36,.1)` | warning bg |
| `--red` | `#b91c1c` | `#f87171` | alert, bad scores |
| `--red-dim` | `rgba(185,28,28,.1)` | `rgba(248,113,113,.12)` | alert bg |

### Misc
| Token | Value | Notes |
|-------|-------|-------|
| `--fs-base` | `16px` | base font size, adjustable via slider |
| `--accent` | `var(--navy)` | alias for current accent color |

---

## Needs Tokenization

### Border-radius scale
| Token idea | v3 values | Used by |
|------------|-----------|---------|
| `--radius-sm` | `3px` | metric cells, omission bars, edit severity tags |
| `--radius-md` | `4px` | badges, edit buttons, zone tags |
| `--radius-lg` | `8px` | chart containers, zones, intro panel, warning banners |
| `--radius-pill` | `16px` | archetype filter pills |
| `--radius-full` | `50%` | summary dots, timeline dots |

### Shadow
| Token idea | v3 value | Used by |
|------------|----------|---------|
| `--shadow-card` | `0 1px 3px rgba(0,0,0,.06)` | zones, intro panel |
| `--shadow-card-strong` | `0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04)` | chart containers |

### Typography
| Token idea | v3 value | Used by |
|------------|----------|---------|
| `--font-heading` | `'DM Serif Display', serif` | h1, h2, brand |
| `--font-body` | `'DM Sans', sans-serif` | body, nav, pills, source names |
| `--font-mono` | `'JetBrains Mono', monospace` | data values, table cells, dates |
| `--fs-tiny` | `.7rem` | zone tags, edit severity |
| `--fs-small` | `.75rem` | metric labels, edit log dates, zone qualifiers |
| `--fs-body` | `.85rem` | nav links, table, zone body, pills |
| `--fs-subtitle` | `.9rem` | subtitles, zone h3 |
| `--fs-h2` | `1.1rem` | chart headings, brand |
| `--fs-stat` | `1.2rem` | stat row values |
| `--fs-h1` | `1.5rem` | page headings |

### Spacing
| Token idea | v3 values | Used by |
|------------|-----------|---------|
| `--gap-xs` | `4px` | waterfall items |
| `--gap-sm` | `8px` | pills, zone h3 label spacing |
| `--gap-md` | `16px` | summary rows, profile-header |
| `--gap-lg` | `24px` | grid-2col columns |
| `--gap-xl` | `40px` | stat row items |
| `--pad-page` | `24px 32px` | page content padding |
| `--pad-card` | `20px` | chart containers |
| `--pad-zone` | `24px` | zone padding |
| `--pad-cell` | `10px 14px` | table cells |
| `--pad-badge` | `3px 12px` | badge padding |
| `--pad-pill` | `4px 14px` | filter pill padding |

### Animation & interaction
| Token idea | v3 value | Used by |
|------------|----------|---------|
| `--transition-fast` | `.12s` | edit buttons, table rows |
| `--transition-base` | `.15s` | nav links, pills |
| `--transition-accordion` | `.3s ease` | intro panel collapse |

### Chart-specific (appear in Chart.js config, not CSS)
| Token idea | v3 value | Used by |
|------------|----------|---------|
| `--chart-grid` | `rgba(0,0,0,.06)` | scatter, radar, volatility chart grids |
| `--chart-line-positive` | `#2d6a4f` | radar current month, volatility trend, scatter quadrant borders |
| `--chart-line-prior` | `#555` | radar previous month |

### Archetype badge colors (4 tokens)
| Token | v3 Light | v3 Dark |
|-------|----------|---------|
| Early Breaker | `#1e3a5f` | `#60a5fa` |
| Noise Generator | `#b91c1c` | `#f87171` |
| Selective but Accurate | `#0f766e` | `#34d399` |
| Consensus Follower | `#64748b` | `#94a3b8` |

---

## How Many Tokens

**Existing CSS vars:** 12
**Needs tokenization:** ~22 (7 shapes/shadows, 10 typography, 3 transition, 5 spacing, 4 archetype badge colors)

**Total:** ~34 tokens for a complete skin system.
