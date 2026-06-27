# Deferred Items

Consolidated list of items explicitly deferred during planning or implementation. This file persists across slices — it is NOT deleted when individual plan documents are archived.

| What | Why deferred | Depends on | Originating slice |
|------|-------------|-----------|-------------------|
| Timeline event markers (day scrubber) | No event data from pipeline agents | SilentAuditorAgent + ConsensusAlignmentAgent output | Slice 5 |
| Vf trend chart | No Vf formula + daily snapshot data | Backend pipeline | Slice 5 |
| Outlier waterfall | No claims through state machine | Backend pipeline | Slice 5 |
| Silent edit log | No SilentAuditorAgent output | Backend pipeline | Slice 5 |
| Tier average radar polygon | No cross-source computation | Backend pipeline | Slice 5 |
| Backend pipeline (Agents 1–4) | Frontend-first build order | Fireworks API key, AMD GPU pod access | Slice 2, 4 |
| Onboarding vocabulary icons (5 terms) | lucide-react icons not selected yet | Icon selection | Slice 3 |
| ~~Vertical filter on Sources page~~ | — | **Resolved in review-03 fix session** | Slice 4 |
| ~~Route DB access pattern~~ | — | **Resolved in review-03 fix session** | Review 03 |
| ~~Pipeline Flow page: scraper start/stop toggle~~ | — | **Resolved in Slice 9** | 8b |
| ~~App header: scraper status indicator~~ | — | **Resolved in Slice 9** | 8b |
