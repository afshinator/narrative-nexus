# ADR-0002: Demo Strategy — No Demo Mode, Seed Script Approach

**Status:** Accepted (supersedes prior version)

## Context

The hackathon demo requires the app to show 90 days of reputation data, claim lifecycles reaching CONSENSUS_ABSORBED and UNRESOLVED states, and daily reputation snapshots — but we only have ~17 days of wall clock time before demo day.

The spec requires a "pre-baked historical corpus" (REQ-096) and says the demo must never show live pipeline runs on unknown data (REQ-101).

## Decision

**There is no demo mode.** The application always works the same way — it reads from SQLite and serves all pages normally. The app is unaware it is being demonstrated.

To populate the database with 90 days of data, a one-shot seed script (`scripts/seed-demo.py`) runs before demo day. It:

1. Accepts a list of ~80 article URLs organized by story (4 stories × ~20 sources each) — real articles from the last 90 days
2. Fetches each URL via `newspaper4k` (same library as the live scraping stack)
3. Feeds extracted text through the same pipeline functions the agents use: embeddings → claim extraction → consensus math → resolution checks
4. Writes database records with timestamps matching the original publication dates, so the 7d/30d/90d resolution checkpoints fire correctly against real timestamps
5. Populates daily reputation snapshots across the full 90-day span

The seed script imports from the same `pipeline/` module as the live scheduler. No separate database, no "demo mode" flag, no static data files, no mock endpoints.

## Consequences

**Positive:**
- One code path — the app never checks "am I in demo mode?"
- The frontend is identical in every context — no conditional rendering
- The database is always the source of truth
- No duplicate data definitions (mock files, static JSON, etc.)
- The seed script doubles as a test fixture generator for the rest of development
- The demo corpus is deterministic and curated, yet processed through the real pipeline

**Negative:**
- The seed script must manually source ~80 article URLs
- Pipeline agents must be callable both from the scheduler and from the seed script (shared module, not inline logic)
- The demo database must be backed up — re-seeding takes pipeline runtime

## Alternatives Considered

1. **Static data file / mock endpoints (prior version of this ADR).** Rejected: introduced a "demo mode" code path, duplicate data definitions, and a switching mechanism that added complexity for no benefit.
2. **Time-lapse the scheduler.** Rejected: would require hacking the scheduler's internal clock, harder to control than a seed script.
3. **Accept ~17 days of data.** Rejected: the 90-day radar morphing, UNRESOLVED claims at day 90, and the full Timeline animation are key demo talking points.
