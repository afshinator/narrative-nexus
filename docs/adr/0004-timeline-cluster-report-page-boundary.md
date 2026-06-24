# ADR-0004: Timeline vs Cluster Report Page Boundary

**Status:** Accepted

## Context

The spec defines two related but separate pages:

- **Timeline** (REQ-088): Horizontal Day 0–90 animation per claim, CONSENSUS_ABSORBED vertical line, UNRESOLVED fade, echo-mimic connections
- **Cluster Report** (REQ-087): 3-zone forensic report (consensus summary / distortion matrix / forensic analysis)

Both pages deal with claims, claim lifecycle states, convergence types (CROSS_SOURCE_CONVERGENT vs SELF_CONSISTENT), and cross-source relationships. Without a clear boundary, the same information could appear on both pages — or worse, fall through the gap between them.

## Decision

The Timeline page handles **temporal sequencing only**: horizontal Day 0–90 axis, claim dots at first-appearance day, absorption line, fade at day 90, echo-mimic connections.

The Cluster Report page handles **per-claim classification**: convergence type table, consensus summary, distortion matrix, forensic analysis.

They are linked via click-through: clicking a claim dot on the Timeline highlights it in the Cluster Report. Convergence badges do NOT appear on timeline dots.

## Consequences

**Positive:**
- Each page has a single clear job (temporal vs classification)
- No overcrowded timeline visualization
- Natural click-through flow for the demo ("see when it happened → understand how it was classified")

**Negative:**
- Requires the cross-page linking mechanism (state sharing or URL params)
- User must navigate between pages to see both temporal and classification views of the same claim

## Alternatives Considered

1. **Embed Cluster Report as a panel inside the Timeline page** — makes the Timeline page too complex and violates the 8-page structure.
2. **Timeline for all claim details** — would overcrowd the visualization and defeat the animation's purpose.
3. **Cluster Report with an embedded mini-timeline** — adds a third visualization to the Cluster Report's 3-zone layout, making it too dense.
