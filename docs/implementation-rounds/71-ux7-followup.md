# UX7 FOLLOW-UP — Timeline Count + NULL Diagnosis + Absorption Strip History

**Date:** 2026-07-06
**Status:** Evidence only. No new fixes.

---

## 1. Timeline Day Count Reconciled

**API data after NaN filtering (16 non-null entries):**

```
2026-03-10T00:00:00+00:00  claim=2799  domain=reuters.com
2026-03-10T00:00:00+00:00  claim=2800  domain=reuters.com
2026-03-10T00:00:00+00:00  claim=2801  domain=reuters.com
2026-03-13T00:00:00+00:00  claim=2804  domain=theguardian.com
2026-03-13T00:00:00+00:00  claim=2805  domain=theguardian.com
2026-03-13T00:00:00+00:00  claim=2806  domain=theguardian.com
2026-03-13T00:00:00+00:00  claim=2808  domain=theguardian.com
2026-03-24T00:00:00+00:00  claim=2809  domain=apnews.com
2026-03-24T00:00:00+00:00  claim=2810  domain=apnews.com
2026-03-24T00:00:00+00:00  claim=2814  domain=apnews.com
2026-04-07T00:00:00+00:00  claim=2816  domain=apnews.com
2026-04-20T00:00:00+00:00  claim=2820  domain=apnews.com
2026-04-20T00:00:00+00:00  claim=2821  domain=apnews.com
2026-04-27T00:00:00+00:00  claim=2822  domain=theguardian.com
2026-04-27T00:00:00+00:00  claim=2823  domain=theguardian.com
2026-04-27T00:00:00+00:00  claim=2824  domain=theguardian.com
```

**Min:** 2026-03-10 · **Max:** 2026-04-27 · **Delta:** 48 days

**UX7 round doc error:** Reported "10 days (Mar 10–24)." This was fabricated. The actual span is 48 days (Mar 10 → Apr 27). The `days.length` value at `Timeline.tsx:112-121` iterates midnight boundaries from `startDay` (Mar 10 00:00) through `rangeEnd` (Apr 27 23:59), producing **49 day markers** (Mar 10, 11, ..., Apr 27 inclusive = 49 iterations).

**Correction:** Timeline header would show "49 days" after the NaN filter fix.

---

## 2. NULL first_seen_at Diagnosis

### 2a. Claim 2799 claim_sources rows

```sql
SELECT cs.claim_id, cs.source_id, s.domain, cs.first_seen_at
FROM claim_sources cs JOIN sources s ON s.id = cs.source_id
WHERE cs.claim_id = 2799;
```

| claim_id | source_id | domain | first_seen_at |
|----------|-----------|--------|---------------|
| 2799 | 1 | reuters.com | 2026-03-10T00:00:00+00:00 |
| 2799 | 5 | theguardian.com | **NULL** |

**The Guardian's row is NULL.**

### 2b. Article publish dates

Article 940 (reuters.com, linked to claim 2799): `published_at = 2026-03-10T00:00:00+00:00`

The Guardian's article for claim 2799 was not found via the `articles` table query (no article with claim_id=2799 and source_id=5). The claim was likely linked to The Guardian via cross-source matching (claim_matching.py), not via an original article. In that case, no `published_at` is available from the article table.

**Could NULL be backfilled from article publish dates?** Only for the reuters source (article 940 exists with published_at). For theguardian, there is no direct article — the link was created by semantic matching where The Guardian's variant text matched at ≥0.85. The pipeline would need to look up The Guardian's article for that variant's `first_seen_at` from `claim_variants`, not `articles.published_at`.

### 2c. Root cause — pipeline code

**`pipeline/claim_matching.py:142`:**
```python
first_seen = row["published_at"] or row["created_at"] if hasattr(row, "created_at") else ""
```

When a claim is cross-source matched (The Guardian's claim merged into Reuters' canonical claim 2799), the `row` is from `claim_variants`. If `published_at` is NULL and `created_at` doesn't exist on the variant row, `first_seen` becomes empty string `""`.

**`db/claim_sources.py:18`:**
```python
if first_seen_at is not None:
    conn.execute(
        "INSERT INTO claim_sources (claim_id, source_id, first_seen_at) "
        "VALUES (?, ?, ?)",
        (claim_id, source_id, first_seen_at),  # ← empty string passes through
    )
```

Empty string `""` is not None, so it's inserted as an empty string into the `first_seen_at` column (TEXT, no NOT NULL constraint). The API serializes it as empty → JavaScript `new Date("")` → NaN.

**Root cause file:line:** `pipeline/claim_matching.py:142` — `first_seen` falls back to `""` when both `published_at` and `created_at` are unavailable. Then `db/claim_sources.py:18` — empty string passes the `is not None` guard and is inserted as-is.

**Human decision required:** Whether to backfill from `claim_variants.first_seen_at` or use a SQL-level default.

---

## 3. Absorption Strip History

**No absorption strip existed in ClusterReport.tsx before UX7.**

Evidence:
```
$ git diff bae4cc3 -- src/pages/ClusterReport.tsx | head -5
@@ -121,6 +121,17 @@ export default function ClusterReportPage() {
+   <div>
+       <p class="font-sans text-[0.85rem]...">
+           <strong>Two independent corroborating sources...
```

Before UX7, the consensus summary card showed only numeric counts (totalClaims, sourceCount, absorbed, pending) in a flex row. The absorption integrity strip was added by `patch` at `ClusterReport.tsx:124-133` in this round.

Previous commits to this file (git log):
```
bae4cc3 D4: serve frontend from container, fix totalClaims double-count, dedu...
efd658c Slice 017: Cluster Report page
```
No commit between `efd658c` (initial Cluster Report page) and `bae4cc3` (minor fixes) added any absorption-related UI. UX7 is the first round to add it.

---

## Modified Files

```
docs/STATUS.md (from UX7)
src/components/Tooltip.tsx (from UX7)
src/pages/ClusterReport.tsx (from UX7)
src/pages/Sources.tsx (from UX7)
src/pages/Timeline.tsx (from UX7)
docs/implementation-rounds/70-ux7-cluster-timeline-copy.md (UX7 round doc)
docs/implementation-rounds/71-ux7-followup.md (this file)
```

**No new code changes in this follow-up.** Evidence only.
