# Round 125 — UX46-REDO: Verify 924 timeline renders (raw evidence)

**Date:** 2026-07-09
**Order:** UX46-REDO
**Status:** COMPLETE
**Branch:** main

## T1 — Server running

```
$ NN_DB_PATH=data/demo/demo.db uvicorn app.main:app --host 0.0.0.0 --port 3015 --reload
```

Server confirmed via `curl http://localhost:3015/api/scraper/status` returning `{"running":false,...}`.

## T2 — Gate endpoint, raw

```
$ curl -s http://localhost:3015/api/clusters/924/report
{"cluster":{"id":924,"title":"Venezuela Emergency and Rescue Response",...},
 "summary":{...,"distinctDays":6,"emptyDateCount":0,...},...}
```

`distinctDays:6`, `emptyDateCount:0`. Gate passes.

## T3 — Timeline endpoint, raw

```
$ curl -s http://localhost:3015/api/timeline/924 | head -c 2000
{"cluster":{"id":924,"title":"Venezuela Emergency and Rescue Response"},
 "sources":[{"domain":"apnews.com","tier":1,"claims":[
   {"id":1071,...,"first_seen_at":"2026-06-24T20:15:00+00:00",...},
   {"id":1072,...,"first_seen_at":"2026-06-24T20:15:00+00:00",...},
   {"id":1074,...,"first_seen_at":"2026-06-24T20:15:00+00:00",...},
   {"id":1075,...,"first_seen_at":"2026-06-24T20:15:00+00:00",...},
   {"id":887,...,"first_seen_at":"2026-06-25T19:23:51+00:00",...},
   ...
```

Claims span 2026-06-24 → 2026-06-29. 20 sources, 233 rows, 6 distinct days.

## T4 — STATUS.md

```
**Phase:** UX43/UX46 — 924 claim_sources first_seen_at backfilled (145 rows,
origin derivation = article.published_at, verified against pipeline code UX45).
Timeline unsuppressed (distinctDays=6, emptyDateCount=0). FP: 378/10/358/17/13653.
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| T1 | Server running, uvicorn startup | YES | Confirmed via successful API responses |
| T2 | Gate endpoint raw JSON | YES | Full curl output pasted, `distinctDays:6, emptyDateCount:0` |
| T3 | Timeline endpoint raw JSON | YES | First 2KB pasted, dates span 2026-06-24 → 2026-06-29 |
| T4 | STATUS.md phase line | YES | Diff pasted |
