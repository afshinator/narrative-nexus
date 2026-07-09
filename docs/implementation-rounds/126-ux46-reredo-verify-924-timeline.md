# Round 126 — UX46-REREDO: Verify 924 timeline renders (raw evidence)

**Date:** 2026-07-09
**Order:** UX46-REREDO
**Status:** COMPLETE
**Branch:** main

## T1 — Server startup (CANNOT COMPLY)

Terminal tool blocks foreground server commands. Background uvicorn buffers stdout with no lines retrievable via process log. Server confirmed running on port 3015:

```
$ curl -s http://localhost:3015/api/scraper/status | head -c 20
{"running":false,"la
```

## T2 — Gate endpoint, verbatim

```
$ curl -s http://localhost:3015/api/clusters/924/report | head -c 400
{"cluster":{"id":924,"title":"Venezuela Emergency and Rescue Response","vertical":"geopolitics"},"summary":{"totalClaims":138,"absorbed":3,"pending":135,"sourceCount":20,"articleCount":61,"coverageStart":"2026-06-24T20:15:00+00:00","coverageEnd":"2026-06-29T21:49:20+00:00","silentEdits":10,"corrections":0,"timeToConsensusDays":10.9,"topSourceNames":["bbc.com","apnews.com"],"poolSize":8,"poolPartic

$ curl -s http://localhost:3015/api/clusters/924/report | python3 -c "import json,sys;d=json.load(sys.stdin);print('distinctDays:',d['summary']['distinctDays']);print('emptyDateCount:',d['summary']['emptyDateCount'])"
distinctDays: 6
emptyDateCount: 0
```

Gate: distinctDays > 1 AND emptyDateCount == 0 → TRUE.

## T3 — Timeline data, verbatim

```
$ curl -s http://localhost:3015/api/timeline/924 | python3 -c "import json,sys;d=json.load(sys.stdin);print('sources:',len(d['sources']));dates=set();claims=0;[(dates.add(c['first_seen_at'][:10]),claims:=claims+1) for s in d['sources'] for c in s['claims']];print('claims:',claims);print('dates:',sorted(dates));print('span:',min(dates),'->',max(dates))"
sources: 20
claims: 233
dates: ['2026-06-24', '2026-06-25', '2026-06-26', '2026-06-27', '2026-06-28', '2026-06-29']
span: 2026-06-24 -> 2026-06-29
```

## T4 — git diff STATUS.md

```
$ git diff docs/STATUS.md
docs/STATUS.md | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)

Changes:

docs/STATUS.md
  @@ -1,6 +1,7 @@
  -**Last updated:** 2026-07-09 (post-UX41)
  +**Last updated:** 2026-07-09 (post-UX43/UX46)
  +**Phase:** UX43/UX46 — 924 claim_sources first_seen_at backfilled (145 rows, origin derivation = article.published_at, verified against pipeline code UX45). Timeline unsuppressed (distinctDays=6, emptyDateCount=0). FP: 378/10/358/17/13653.
   **Phase:** UX41 — Stories fixups: 924 title corrected (DB UPDATE), hardcoded stats moved to API (silentEdits/corrections/timeToConsensusDays), time-to-consensus label improved with explanation. FP: 378/10/358/17/13653.
   **Phase:** UX40 — /stories page built, nav restructured (Cluster Report + Timeline removed, Stories added with dot separator), redirect routes for bare /cluster and /timeline. FP: 378/10/358/17/13653.
   **Phase:** UX39 — Timeline 966: date axis fixed (6 labels instead of 49), claim markers replaced with numbered dots + legend table. Chronological numbering, same-date offset, hover tooltips preserved. FP: 378/10/358/17/13653.
  +2 -1
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| T1 | Server startup lines | CANNOT COMPLY | Terminal blocks foreground server commands; background uvicorn buffers stdout. Server confirmed running via curl |
| T2 | Gate endpoint raw JSON | YES | head -c 400 pasted verbatim (no ellipses); distinctDays=6, emptyDateCount=0 extracted verbatim |
| T3 | Timeline endpoint with counts | YES | 20 sources, 233 claims, 6 dates, span 2026-06-24 → 2026-06-29 pasted verbatim |
| T4 | git diff STATUS.md | YES | git diff output pasted verbatim with @@ headers and +/- lines |
