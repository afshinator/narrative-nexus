# FV4 — Three Fixes

**Date:** 2026-07-06
**Commit:** `6a2dc50`

---

## F1 — Cluster 966 Reconcile

### COUNT(*)

```
sqlite3 data/demo/demo.db "SELECT COUNT(*) FROM claims WHERE cluster_id = 966"
→ 19
```

### Claim 2818 Absent

```
sqlite3 data/demo/demo.db "SELECT id FROM claims WHERE id = 2818"
→ (empty — no rows)

sqlite3 data/demo/demo.db "SELECT COUNT(*) FROM claim_sources WHERE claim_id = 2818"
→ 0
```

Claim 2818 was deleted in FV2.4. No remnants in claims or claim_sources.

### "2 ABSORBED" Explanation

The cluster report API (`app/main.py:402-404`) counts absorbed claims per source via GROUP BY:

```sql
SELECT s.domain, COUNT(DISTINCT cl.id) AS claims,
       SUM(CASE WHEN cl.state = 'CONSENSUS_ABSORBED' THEN 1 ELSE 0 END) AS absorbed
FROM claims cl
JOIN claim_sources cs ON cs.claim_id = cl.id
JOIN sources s ON s.id = cs.source_id
WHERE cl.cluster_id = 966
GROUP BY s.id
```

Claim 2799 appears in claim_sources under TWO sources:
```
claim_id=2799, source_id=1 (reuters)
claim_id=2799, source_id=5 (theguardian)
```

Per-source GROUP BY result:
| Source | Claims | Absorbed |
|--------|--------|----------|
| reuters.com | 4 | 1 |
| apnews.com | 8 | 0 |
| theguardian.com | 8 | 1 |

Python code (`app/main.py:416`): `total_absorbed = sum(s["absorbed"] for s in sources)` → 1+0+1 = 2.

**Unique absorbed claim count:**
```
SELECT COUNT(DISTINCT id) FROM claims WHERE cluster_id = 966 AND state = 'CONSENSUS_ABSORBED'
→ 1
```

The "2 ABSORBED" is a per-source double-count of a single merged claim (2799) that spans two sources in claim_sources. The report is structurally correct per-source but overcounts when summed.

### Tie-Out

| Metric | Value |
|--------|-------|
| Claims in cluster 966 | 19 |
| Claim 2818 exists | No (deleted) |
| Unique absorbed | 1 (claim 2799) |
| Reported absorbed | 2 (per-source GROUP BY sum) |
| Fingerprint | 378/10/358/17/13653 (unchanged) |

---

## F2 — Archetype Median Canon

### Problem

FV3 identified a median conflict:
- `/api/sources` (stored snapshot): median 52/48 → theguardian = NOISE_GENERATOR
- `/api/sources/{id}/profile` (fresh compute from ALL dates): median 76/0 → theguardian = EARLY_BREAKER

The profile endpoint computed panelMedian from all historical rows, producing different archetypes than the pipeline stored in snapshots.

### Fix

Added `_get_latest_archetype()` to `app/main.py` and included `"archetype"` in the profile response:

```python
def _get_latest_archetype(conn, source_id: int, vertical: str) -> str | None:
    """Return the stored archetype from the latest snapshot for source+vertical."""
    row = conn.execute(
        "SELECT archetype FROM snapshots "
        "WHERE source_id = ? AND vertical = ? "
        "ORDER BY date DESC LIMIT 1",
        (source_id, vertical),
    ).fetchone()
    return row["archetype"] if row else None
```

Profile response now includes:
```python
return {
    "snapshots": snapshots,
    "tierAvg": tier_avg,
    "panelMedian": panel_median,
    "archetype": _get_latest_archetype(conn, source_id, vertical),  # ← NEW
    "events": events,
    "edits": edits,
    "claimSummary": claim_summary,
}
```

### Verification

```
GET /api/sources/5/profile?vertical=geopolitics
→ archetype: "NOISE_GENERATOR"

GET /api/sources
→ theguardian archetypes: {"geopolitics": "NOISE_GENERATOR", ...}
```

Both endpoints now return the same canonical archetype.

### Diff

```
app/main.py | 21 +++++++++++++++++++++
 (+21/-0)
```

---

## F3 — Cluster 966 Title

### Before

```
sqlite3 data/demo/demo.db "SELECT id, title FROM clusters WHERE id = 966"
→ 966|R2.9c temporary — articles 940-945
```

### After

```
sqlite3 data/demo/demo.db "SELECT id, title FROM clusters WHERE id = 966"
→ 966|US-Iran War: March Escalation & April Ceasefire
```

```sql
UPDATE clusters SET title = 'US-Iran War: March Escalation & April Ceasefire' WHERE id = 966;
```

---

## Commit

```
6a2dc50 FV4: 966 reconcile, archetype canon, cluster title

 app/main.py       |  21 +++++++++++++++++++++
 data/demo/demo.db | Bin 4763648 -> 4763648 bytes
 docs/STATUS.md    |  11 ++++++-----
 3 files changed, 27 insertions(+), 5 deletions(-)
```

---

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|---|---|---|
| F1 | COUNT(*) 966 claims | YES | 19 |
| F1 | 2818 absent | YES | 0 rows claims, 0 claim_sources |
| F1 | Explain 2 vs 1 absorbed | YES | claim_sources per-source double-count of merged claim 2799 |
| F2 | Profile returns stored archetype | YES | `_get_latest_archetype` → NOISE_GENERATOR |
| F2 | Both endpoints match | YES | /api/sources and /api/profile agree |
| F3 | Cluster title renamed | YES | "US-Iran War: March Escalation & April Ceasefire" |
| Commit | git log -1 --stat | YES | `6a2dc50`, 3 files +27/-5 |
| ROUND | Three fixes complete | YES | All committed |
| Render | Verification status | UNKNOWN | Not claimed — browser tool unavailable |

---

## STOP
