# ADR-0001: Multi-Vertical Consensus Threshold Evaluation

**Status:** Accepted

## Context

A story can match multiple topic verticals (GEOPOLITICS, ECONOMICS, TECHNOLOGY). Each vertical has a different default consensus threshold (65%, 75%, 75%). The spec requires thresholds to be configurable at runtime and stored per cluster run for historical validity.

The question: when a claim belongs to a multi-vertical story, which threshold governs its consensus status?

## Decision

Claims in multi-vertical stories are evaluated against **each vertical's consensus threshold independently**. A claim enters the consensus baseline for a vertical if it clears that vertical's threshold.

In the UI, clusters display which vertical(s) they were classified under so the user can see which threshold applies.

## Consequences

**Positive:**
- Most honest representation — a geopolitics story with economic implications gets judged on both dimensions
- No information loss from forcing a "primary vertical" classification
- Enables cross-vertical analysis (e.g., a source that's reliable in tech but noisy in geopolitics)

**Negative:**
- Increased storage/computation per claim (N evaluations instead of 1)
- UI must convey which vertical's threshold is being shown at a glance

## Alternatives Considered

1. **Primary vertical only** — assign each story a single "primary" vertical and use only its threshold. Rejected because it loses information and a story's vertical classification is inherently fuzzy.
2. **Strictest threshold wins** — use the highest threshold among matched verticals. Rejected because it penalizes sources in multi-dimensional stories.
3. **Threshold averaged across matched verticals** — conceptually unclear and hard to reason about.
