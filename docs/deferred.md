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
| ~~ReputationScore extraction to shared location~~ | Was single consumer | **Resolved in Slice 5** | Slice 4 |
| Vertical filter on Sources page | Vertical selector component didn't exist | Vertical picker built (Slice 5) — partially resolved | Slice 4 |
| Onboarding vocabulary icons (5 terms) | lucide-react icons not selected yet | Icon selection | Slice 3, CONTEXT.md |
| Worker `requirements.txt` | Worker is a stub container (M1 ponytail skip) | Worker build (backend phase) | M1 |
| Multi-stage Dockerfile | Current workflow builds before Docker (M1 ponytail skip) | Container build change | M1 |
