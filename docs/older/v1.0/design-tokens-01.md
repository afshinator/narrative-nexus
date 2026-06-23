1. Archival Editorial (Current v3) — Dual Mode
This theme retains both light and dark versions. It honors your established design brief while providing smooth, high-contrast toggling between traditional reading-room tones and modern dark journalism palettes.

```
:root[data-theme="archival-editorial"] {
  /* --- Colors (Light Mode Default) --- */
  --bg: #f5f3ee;
  --surface: #ffffff;
  --surface2: #ece8e0;
  --border: #d8d4cc;
  
  --text: #1c1a16;
  --text-dim: #7a7568;
  
  --navy: #1e3a5f;
  --navy-dim: rgba(30, 58, 95, .08);
  --forest: #2d6a4f;
  --forest-dim: rgba(45, 106, 79, .1);
  --amber: #b8860b;
  --amber-dim: rgba(184, 134, 11, .1);
  --red: #b91c1c;
  --red-dim: rgba(185, 28, 28, .1);

  --badge-early-breaker: #1e3a5f;
  --badge-noise-generator: #b91c1c;
  --badge-selective: #0f766e;
  --badge-follower: #64748b;

  --chart-grid: rgba(0, 0, 0, .06);
  --chart-line-positive: #2d6a4f;
  --chart-line-prior: #555555;

  /* --- Shapes, Shadows, Typography --- */
  --radius-sm: 3px;
  --radius-md: 4px;
  --radius-lg: 8px;
  --radius-pill: 16px;
  --radius-full: 50%;
  --shadow-card: 0 1px 3px rgba(0, 0, 0, .06);
  --shadow-card-strong: 0 1px 3px rgba(0, 0, 0, .06), 0 1px 2px rgba(0, 0, 0, .04);

  --font-heading: 'DM Serif Display', serif;
  --font-body: 'DM Sans', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  --transition-fast: .12s;
  --transition-base: .15s;
  --transition-accordion: .3s ease;
}

/* Archival Editorial - Dark Mode Variant */
@media (prefers-color-scheme: dark) {
  :root[data-theme="archival-editorial"] {
    --bg: #0c0b12;
    --surface: #14131d;
    --surface2: #1e1c2e;
    --border: #2a2840;
    
    --text: #e6e4f0;
    --text-dim: #8a86a0;
    
    --navy: #60a5fa;
    --navy-dim: rgba(59, 130, 246, .12);
    --forest: #34d399;
    --forest-dim: rgba(52, 211, 153, .1);
    --amber: #fbbf24;
    --amber-dim: rgba(251, 191, 36, .1);
    --red: #f87171;
    --red-dim: rgba(248, 113, 113, .12);

    --badge-early-breaker: #60a5fa;
    --badge-noise-generator: #f87171;
    --badge-selective: #34d399;
    --badge-follower: #94a3b8;

    --chart-grid: rgba(255, 255, 255, .08);
    --chart-line-positive: #34d399;
    --chart-line-prior: #8a86a0;
  }
}
```

---

2. Tactical Intel (OSINT Terminal) — Pure Dark Mode Only
To protect the rapid, operational command-center aesthetic, this block completely drops light mode hooks. If selected, it locks the app into high-contrast dark space regardless of global user agent settings.

```
:root[data-theme="tactical-intel"] {
  /* --- Colors (Locked Dark Environment) --- */
  --bg: #0a0c10;
  --surface: #0f141c;
  --surface2: #161b22;
  --border: #30363d;
  
  --text: #f0f6fc;
  --text-dim: #8b949e;
  
  --navy: #58a6ff;
  --navy-dim: rgba(88, 166, 255, .15);
  --forest: #00e676;
  --forest-dim: rgba(0, 230, 118, .12);
  --amber: #ffb300;
  --amber-dim: rgba(255, 179, 0, .12);
  --red: #ff1744;
  --red-dim: rgba(255, 23, 68, .15);

  --badge-early-breaker: #21262d;
  --badge-noise-generator: #301117;
  --badge-selective: #0e2a1a;
  --badge-follower: #21262d;

  --chart-grid: rgba(48, 54, 61, .6);
  --chart-line-positive: #00e676;
  --chart-line-prior: #484f58;

  /* --- Structural Rigidity --- */
  --radius-sm: 1px;
  --radius-md: 2px;
  --radius-lg: 4px;
  --radius-pill: 4px; /* Hard cornered indicators */
  --radius-full: 50%;
  --shadow-card: none;
  --shadow-card-strong: none;

  --font-heading: 'Inter', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
  --font-mono: 'SF Mono', monospace;

  --transition-fast: .05s;
  --transition-base: .08s;
  --transition-accordion: .15s cubic-bezier(0, 0, 0.2, 1);
}
```

---

3. Clinical Ledger (Bureaucratic Registry) — Pure Light Mode Only
Inverting this archetype would break its clinical, "official printed documentation" identity. It uses harsh black borders and strips emotional pass/fail coloring completely out of the interface to focus strictly on pure structural alignment.

```
:root[data-theme="clinical-ledger"] {
  /* --- Colors (Locked White-Paper Starkness) --- */
  --bg: #f2f2f2;
  --surface: #ffffff;
  --surface2: #ffffff;
  --border: #1a1a1a; 
  
  --text: #000000;
  --text-dim: #666666;
  
  /* Neutralized indicator states remove psychological value judgments */
  --navy: #1a1a1a;
  --navy-dim: rgba(0, 0, 0, .05);
  --forest: #333333;
  --forest-dim: rgba(0, 0, 0, .03);
  --amber: #555555;
  --amber-dim: rgba(0, 0, 0, .04);
  --red: #000000;
  --red-dim: rgba(0, 0, 0, .08);

  --badge-early-breaker: #000000;
  --badge-noise-generator: #333333;
  --badge-selective: #555555;
  --badge-follower: #777777;

  --chart-grid: #1a1a1a;
  --chart-line-positive: #000000;
  --chart-line-prior: #888888;

  /* --- Absolute Brutalism Shapes --- */
  --radius-sm: 0px;
  --radius-md: 0px;
  --radius-lg: 0px;
  --radius-pill: 0px;
  --radius-full: 0px; /* Forces square scatter-plot nodes */
  --shadow-card: none;
  --shadow-card-strong: none;

  --font-heading: 'Neue Haas Grotesk', Arial, sans-serif;
  --font-body: 'Neue Haas Grotesk', Arial, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  --transition-fast: 0s;
  --transition-base: 0s;
  --transition-accordion: 0s;
}
```

---

4. Signal Field (Spectrum & Diffusion) — Dual Mode
Because this layout relies on translucent fluid backdrops and gradients rather than raw value extremes, it effortlessly shifts between an airy glassmorphic light space and a glowing neon dark space.

```
:root[data-theme="signal-field"] {
  /* --- Colors (Fluid Light Mode Default) --- */
  --bg: #fafbfe;
  --surface: rgba(255, 255, 255, 0.8);
  --surface2: #f1f4fa;
  --border: #e2e8f0;
  
  --text: #1e293b;
  --text-dim: #64748b;
  
  --navy: #3b82f6;
  --navy-dim: rgba(59, 130, 246, .08);
  --forest: #06b6d4; 
  --forest-dim: rgba(6, 182, 212, .08);
  --amber: #f59e0b;
  --amber-dim: rgba(245, 158, 11, .08);
  --red: #d946ef; /* Chromatic magenta shift for narrative fracture alerts */
  --red-dim: rgba(217, 70, 239, .08);

  --badge-early-breaker: #3b82f6;
  --badge-noise-generator: #d946ef;
  --badge-selective: #06b6d4;
  --badge-follower: #94a3b8;

  --chart-grid: rgba(226, 232, 240, .8);
  --chart-line-positive: #3b82f6;
  --chart-line-prior: #cbd5e1;

  /* --- Organic Pillowed Shapes --- */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 16px;
  --radius-pill: 9999px;
  --radius-full: 50%;
  --shadow-card: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  --shadow-card-strong: 0 10px 15px -3px rgba(59, 130, 246, 0.03);

  --font-heading: 'Plus Jakarta Sans', sans-serif;
  --font-body: 'Plus Jakarta Sans', sans-serif;
  --font-mono: 'Geist Mono', monospace;

  --transition-fast: .2s cubic-bezier(0.16, 1, 0.3, 1);
  --transition-base: .3s cubic-bezier(0.16, 1, 0.3, 1);
  --transition-accordion: .4s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Signal Field - Dark Mode Variant */
@media (prefers-color-scheme: dark) {
  :root[data-theme="signal-field"] {
    --bg: #090d16;
    --surface: rgba(15, 23, 42, 0.8);
    --surface2: #1e293b;
    --border: #1e293b;
    
    --text: #f8fafc;
    --text-dim: #94a3b8;
    
    --navy: #60a5fa;
    --navy-dim: rgba(96, 165, 250, .1);
    --forest: #22d3ee;
    --forest-dim: rgba(34, 211, 238, .1);
    --amber: #fbbf24;
    --amber-dim: rgba(251, 191, 36, .1);
    --red: #f472b6;
    --red-dim: rgba(244, 114, 182, .1);

    --badge-early-breaker: #60a5fa;
    --badge-noise-generator: #f472b6;
    --badge-selective: #22d3ee;
    --badge-follower: #475569;

    --chart-grid: rgba(30, 41, 59, .8);
    --chart-line-positive: #60a5fa;
    --chart-line-prior: #475569;
  }
}
```

---

- note: The Toggle Component Mismatch: If you use a standard HTML checkbox or button toggle for your theme picker that assumes a strict binary value (checked === dark-mode), your state engine will desync when switching themes. For instance, if a user changes the main skin token to clinical-ledger, your toggle component might still say "Dark Mode Enabled" under the hood even though the interface has forced itself to a bright light configuration via the CSS overrides. You will want to ensure your UI controller handles active skin settings and dark/light color states as distinct variables.