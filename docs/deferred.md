# Deferred Items

Consolidated list of items explicitly deferred during planning or implementation. This file persists across slices — it is NOT deleted when individual plan documents are archived.

| What | Why deferred | Depends on | Originating slice |
|------|-------------|-----------|-------------------|
| Timeline event markers (day scrubber) | No event data from pipeline agents | SilentAuditorAgent + ConsensusAlignmentAgent output | Slice 5 |
| Vf trend chart | No Vf formula + daily snapshot data | Backend pipeline | Slice 5 |
| Outlier waterfall | No claims through state machine | Backend pipeline | Slice 5 |
| Silent edit log | No SilentAuditorAgent output | Backend pipeline | Slice 5 |
| Tier average radar polygon | No cross-source vertical classification | Backend pipeline (Agents 1, 2) | Slice 5 |
| Backend pipeline (Agents 1–4) | Frontend-first build order | Provider abstraction layer (any configured provider) | Slice 2, 4 |
| Google News opaque redirect URLs | 4 sources (Reuters, AP, NHK World, Global Times) use Google News RSS — URLs are opaque redirects, not canonical source URLs | Native RSS feeds for these sources | Review 03 (H04) |
| ~~Onboarding vocabulary icons (5 terms)~~ | — | **Resolved (6 terms, all have lucide-react icons)** | Slice 3 |
| ~~Vertical filter on Sources page~~ | — | **Resolved in review-03 fix session** | Slice 4 |
| ~~Route DB access pattern~~ | — | **Resolved in review-03 fix session** | Review 03 |
| ~~Pipeline Flow page: scraper start/stop toggle~~ | — | **Resolved in Slice 9** | 8b |
| ~~App header: scraper status indicator~~ | — | **Resolved in Slice 9** | 8b |
