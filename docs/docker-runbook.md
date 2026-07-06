# Docker Runbook — Narrative Nexus

## Human Commands (run from clean clone)

```bash
# 1. Clone (skip if already in repo)
git clone <repo-url> && cd narrative-nexus

# 2. Build
docker compose build

# 3. Start (Ctrl+C to stop)
docker compose up

# 4. Verify — wait ~10s for startup, then:
curl -s http://localhost:8000/api/sources | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"
# → 37

curl -s http://localhost:8000/api/clusters/966/report | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'absorbed={d[\"absorbed\"]}, totalClaims={d[\"totalClaims\"]}')"
# → absorbed=1, totalClaims=19
```

## Notes
- Demo DB is baked into the image — no volume mount, no data loss risk
- Pipeline/scheduler is OFF by default (no `NN_ENABLE_PIPELINE` in compose env)
- All 6 radar dimensions pre-computed for 37 sources × 3 verticals
