# Deferred Items

Consolidated list of items explicitly deferred during planning or implementation. This file persists across slices — it is NOT deleted when individual plan documents are archived.

| What | Why deferred | Depends on | Originating slice |
|---|---|---|---|
| ~~Vf trend chart~~ | — | **Implemented in Slice 012** | Slice 5 |
| ~~Tier average radar polygon~~ | — | **Implemented in Slice 012** | Slice 5 |
| ~~Timeline event markers (day scrubber)~~ | — | **Unblocked by Slice 013 (absorbed_at + silent_edits table)** | Slice 5 |
| ~~Outlier waterfall~~ | — | **Unblocked by Slice 013 (determine_state already returns UNRESOLVED). Data-dependent: needs clusters with pool_size≥2 AND baseline below threshold.** | Slice 5 |
| ~~Silent edit log~~ | — | **Unblocked by Slice 013 (silent_edits table + Agent 4 writes)** | Slice 5 |
| ~~Backend pipeline (Agents 1–4)~~ | — | **Implemented (all 4 agents operational)** | Slice 2, 4 |
| Google News opaque redirect URLs | 4 sources (Reuters, AP, NHK World, Global Times) use Google News RSS — URLs are opaque redirects, not canonical source URLs | Native RSS feeds for these sources | Review 03 (H04) |
| ~~Onboarding vocabulary icons (5 terms)~~ | — | **Resolved (6 terms, all have lucide-react icons)** | Slice 3 |
| ~~Vertical filter on Sources page~~ | — | **Resolved in review-03 fix session** | Slice 4 |
| ~~Route DB access pattern~~ | — | **Resolved in review-03 fix session** | Review 03 |
| ~~Pipeline Flow page: scraper start/stop toggle~~ | — | **Resolved in Slice 9** | 8b |
| ~~App header: scraper status indicator~~ | — | **Resolved in Slice 9** | 8b |
