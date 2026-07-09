# Round 117 — DIAGNOSTIC: Timeline 966 date axis + claim label defects

**Date:** 2026-07-09
**Order:** DIAGNOSTIC — READ-ONLY
**Status:** COMPLETE
**Branch:** main

## Defect A — Date axis unreadable (priority)

### Symptoms

The horizontal date axis on `/timeline/966` renders all 49 calendar days in a 48-day span as overlapping text. Dates like "Mar 10", "Mar 11", "Mar 12" through "Apr 27" are stacked on top of each other.

### Data

```
6 distinct dates over 48 days: 2026-03-10, 03-13, 03-24, 04-07, 04-20, 04-27
49 day labels rendered (every calendar day)
20 claims across 3 sources (reuters:4, theguardian:8, apnews:8)
```

### Root cause

`Timeline.tsx:121–128` generates one label for **every calendar day** in the span:

```tsx
const startDay = new Date(rangeStart);
startDay.setHours(0, 0, 0, 0);
const days: Date[] = [];
for (
    let d = new Date(startDay);
    d.getTime() <= rangeEnd;
    d.setDate(d.getDate() + 1)
) {
    days.push(new Date(d));
}
```

This produces 49 labels for 6 distinct dates with data. Each label is rendered at:

```tsx
style={{
    left: `${Math.max(0, pct)}%`,
    transform: "translateX(-50%)",
}}
```

At ~1020px available width (1340px max container minus 180px source label margin minus padding), adjacent-day labels are ~21px apart. But "Mar 10" at 0.75rem font-size is ~55px wide — well beyond the spacing. Even non-adjacent labels overlap at these densities.

No overlap-avoidance filter or stagger exists. No text rotation. No tick-limiting logic.

### Fix scope (smallest defensible)

Filter `days` to only include dates that actually have claim data:

```tsx
// Only label days that have claims — avoids 49-label overlap
const claimDates = new Set(
    data.sources.flatMap(s =>
        s.claims.map(c => c.first_seen_at.split('T')[0])
    )
);
const days = [...claimDates].sort().map(d => new Date(d + 'T00:00:00'));
```

This reduces 49 labels to 6 — clean, readable, no overlap. Can be refined later with major-tick/minor-tick grid, but 6 labels is the lazy correct fix.

## Defect B — Claim label overflow (secondary)

### Symptoms

Full claim text renders inline truncated with ellipsis:

"Residential areas in Tehran were hit. kes…"
"The 82nd Airborne is based at Fort Bragg, N…"

Only 3 rows exist (reuters, theguardian, apnews). theguardian and apnews have 8 claims each, stacked horizontally in a single row that can show at most 280px worth of text per claim. Same-date claims overlap on the same x position.

### Rendering code

`Timeline.tsx:232–244`:
```tsx
<span
    title={claim.text}
    className="absolute top-1 block h-7 max-w-[280px]
      cursor-default overflow-hidden text-ellipsis
      whitespace-nowrap rounded px-2 py-0.5
      font-sans text-[0.75rem] leading-relaxed ..."
    style={{ left: `${Math.max(0, Math.min(100, pct))}%` }}
>
    {claim.text}
</span>
```

- `max-w-[280px]`: caps at 280px regardless of container width
- `whitespace-nowrap` + `overflow-hidden` + `text-ellipsis`: single-line truncation
- `position: absolute; left: pct%`: same-date claims overlap
- `title={claim.text}`: tooltip fallback (visible on hover)

Longest claim: "The Pentagon described the day's strikes as involving more fighters, bombers, an..." (93 chars, rest truncated). Full claim texts available in tooltip and API response.

### Handoff direction

Numbered/short markers on the timeline itself + a legend below mapping marker → full claim text.

### Fix scope

Replace claim card spans with small numbered dots/markers. Add a claims legend table below the timeline rows. Each source row gets: vertical dot-line at each claim's date position, with a small number on the dot. Below the timeline, a collapsible or always-visible legend:

```
1. On Tuesday, the U.S. and Israel launched airstrikes against Iran...
2. Iran's Revolutionary Guards threatened to block all Middle East oil shipments...
...
```

This is a moderate refactor — the claim positioning logic stays but the rendering element changes from `<span>` with full text to a dot with a number.

## Combined fix estimate

Both defects on the same page. A single round can address both:

1. Defect A: reduce day labels to `claimDates` set (2-line change, line 121-128)
2. Defect B: replace claim cards with numbered markers + legend table (new component, ~40 lines)

Defect A is trivial. Defect B is moderate but self-contained. Together: one pass on Timeline.tsx.
