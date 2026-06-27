# Adversarial Code Review 03 — Narrative Nexus

**Date:** 2026-06-26  
**Scope:** All implemented code (frontend, backend, pipeline, database, tests)  
**Method:** Every finding verified by reading actual source — no assumptions, no guesses  
**Spec reference:** `docs/design-v1.2.md` (v1.2), `spec/requirements.md` (tagged requirements), `docs/plan/` (plan docs for each slice)

---

## Root Cause Classification

Throughout this document, each finding is tagged with a root cause category:

| Category | Meaning |
|---|---|
| **DESIGN-GAP** | The design doc or spec was ambiguous or silent on a detail that led to the bug |
| **WRONG-IMPL** | The spec was clear, but the implementation didn't follow it |
| **KNOWN-TRADEOFF** | The plan docs documented this as a deliberate compromise |
| **OVERSIGHT** | The developer knew the pattern but forgot to apply it correctly |
| **INCOMPLETE** | The feature was deliberately left for a future slice |
| **COMPOUNDING** | Two individually harmless decisions combined to create a bug |

---

## 🔴 CRITICAL (production-blocking)

### C01. API routes query empty in-memory databases

**File:** `app/main.py` (lines 48, 58, 69, 79, 89, 99)  
**Spec violation:** Unspecified — but the API cannot serve data, making the frontend non-functional

Every route handler:
```python
conn = get_db()  # no path argument → defaults to ":memory:"
```

`get_db()` defaults to `:memory:` (`db/connection.py` line 17). The lifespan context correctly reads `NN_DB_PATH` from env (`app/main.py` line 19) and passes it to `ScraperScheduler`, but none of the route handlers use it. They create a fresh empty in-memory database on every request, which is discarded on `conn.close()`.

Meanwhile, `scheduler.py` line 79 correctly calls `get_db(self.db_path)` with the persistent path, so the scraper writes to `data/nn.db` — but no API endpoint ever reads from it.

**Fix:** Pass `NN_DB_PATH` to routes. Either store the db path in `request.app.state` during lifespan, or create a dependency that reads the env var:

```python
def get_db_conn(request: Request):
    db_path = request.app.state.db_path
    conn = get_db(db_path)
    try:
        yield conn
    finally:
        conn.close()
```

### C02. Schema crash loop — `CREATE TABLE` without `IF NOT EXISTS`

**File:** `db/schema.sql` (lines 7, 17, 33, 41, 58, 66)  
**Spec violation:** REQ-112 (SQLite WAL mode is sufficient — but the code can't stay running)

All 6 `CREATE TABLE` statements lack `IF NOT EXISTS`. The schema is loaded by `load_schema()` in `db/connection.py` (line 13) on every `get_db()` call via `executescript`. On the first request the tables are created; on the second request the crash hits:

```sql
CREATE TABLE sources (...)   -- line 7
CREATE TABLE articles (...)  -- line 17
CREATE TABLE clusters (...)  -- line 33
CREATE TABLE claims (...)    -- line 41
CREATE TABLE claim_sources (...) -- line 58
CREATE TABLE snapshots (...) -- line 66
```

The only `IF NOT EXISTS` in the file is on the index at line 30 — the developer knew about the pattern but only applied it to one statement.

**Fix:** Add `IF NOT EXISTS` to all 6 `CREATE TABLE` statements, and move schema loading to application startup (once, not per-connection).

### C03. Investigate page silently discards user queries

**File:** `src/pages/Investigate.tsx` (lines 32-39)  
**Spec violation:** REQ-118, REQ-119, REQ-120, REQ-122

```typescript
function handleSubmit() {
  const trimmed = query.trim();
  if (!trimmed) return;
  setSubmitted(true);
  setQuery("");  // query cleared
  // No API call. No store.addAdHocResult(). Nothing.
}
```

Spec REQ-118 requires: "Ad-hoc query results must display extracted atomic claims from pipeline stages 1 through 3." REQ-119 requires cross-source matches and consensus baseline comparison. REQ-120 requires localStorage persistence. REQ-122 requires read-only pipeline execution.

None of these happen. The query is discarded, a transient "Submitted" message appears for 3 seconds, and no backend request is made. The `adHocResults` array in the store can only be populated via direct `useStore.setState()` calls — there is no code path that produces results.

The test at `src/__tests__/investigate.test.tsx` (line 66, "does NOT store empty result on submit") confirms this behavior is intentional in the current code — but it directly violates the spec.

**Fix:** The `handleSubmit` function needs to:
1. Generate a result ID and timestamp
2. Call `addAdHocResult()` with the query text (even if `claims: []` initially)
3. Submit the query to a backend endpoint (or queue it for the pipeline)
4. Store the result in the Zustand store for persistence via the persist middleware

### C04. Consensus agent crashes on datetime subtraction

**File:** `pipeline/agent3_consensus.py` (lines 62-63)

```python
def _days_since(date_str: str | None) -> int:
    dt = datetime.fromisoformat(date_str)    # → naive datetime (no tz)
    now = datetime.now(timezone.utc)          # → aware datetime
    return (now - dt).days                    # TypeError
```

`datetime.fromisoformat()` on the stored ISO string (e.g. `"2024-01-15 10:30:00"`, naive) returns a naive datetime. `datetime.now(timezone.utc)` returns an aware datetime. Python prohibits subtracting these. The consensus agent crashes on every claim with a valid `created_at` value.

**Fix:** Make the parsed datetime aware:
```python
dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
```

### C05. RSS dates crash consensus agent before reaching the state machine

**File:** `pipeline/scraper.py` (line 53) → `pipeline/agent3_consensus.py` (line 61)

The scraper stores the raw RSS `published` field:
```python
"published_at": published if published else datetime.now(timezone.utc).isoformat(),
```

Feedparser returns RFC 2822 dates like `"Mon, 15 Jan 2024 10:30:00 GMT"`. `datetime.fromisoformat()` in `_days_since` cannot parse this — it raises `ValueError`.

Feedparser also provides `entry.published_parsed` (a `time.struct_time`) which is completely ignored.

**Fix:** In `scraper._normalize()`, prefer `published_parsed` and convert to ISO format:
```python
import time, email.utils
if entry.get("published_parsed"):
    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
elif entry.get("published"):
    # Try parsing RFC 2822 as fallback
    parsed = email.utils.parsedate_to_datetime(entry["published"])
    published_at = parsed.isoformat() if parsed else datetime.now(timezone.utc).isoformat()
```

---

## 🟠 HIGH

### H01. Polarity colors are inverted for R_speed, R_frame, R_edit

**File:** `src/utils/polarity.ts` (lines 7-12)  
**Spec violation:** REQ-082 ("Polarity binding must assign color by dimension using getPolarityColor")

```typescript
export function getPolarityColor(dimension: string, percentile: number): string {
  if (TRAIT_DIMENSIONS.has(dimension)) return "var(--nn-slate)";
  if (percentile >= 66) return "var(--nn-teal)";    // high = good
  if (percentile >= 33) return "var(--nn-amber)";
  return "var(--nn-red)";                            // low = bad
}
```

Per the design spec (§4, Reputation Dimensions):
- `R_speed`: "Graded — low (days) is favorable"
- `R_frame`: "Graded — low stddev is favorable"
- `R_edit`: "Graded — low is favorable"

A source with `R_speed: 10` (fast validation = good) gets colored `red` (bad). A source with `R_speed: 90` (slow = bad) gets `teal` (good). The function has no knowledge of `INVERTED_DIMS`.

This surfaces on the SourceProfile page's `StatPanel` (line 218) where `getPolarityColor(dim.key, value)` is called without inversion.

**Fix:** Pass the dimension context or invert the value before calling for inverted dims:
```typescript
export function getPolarityColor(
  dimension: string,
  value: number,
  invertedDims?: Set<string>,
): string {
  if (TRAIT_DIMENSIONS.has(dimension)) return "var(--nn-slate)";
  const effectiveValue = invertedDims?.has(dimension) ? 100 - value : value;
  if (effectiveValue >= 66) return "var(--nn-teal)";
  if (effectiveValue >= 33) return "var(--nn-amber)";
  return "var(--nn-red)";
}
```

### H02. Tier average on radar chart is not polarity-inverted

**File:** `src/pages/SourceProfile.tsx` (lines 267-272, 305-308)

The `toRadarValues` helper correctly inverts `INVERTED_DIMS` for the current and baseline data. But the `tierAvg` dataset is plotted raw:

```typescript
...(tierAvg ? [{
  label: "Tier avg",
  data: tierAvg,        // NOT inverted!
  // ...
}] : [])
```

If a source has `R_speed: 20` and the tier average is `30`, the current line shows `80` (inverted) but the tier average line shows `30`. The comparison line is in the wrong position for R_speed, R_frame, and R_edit.

**Fix:** Apply the same inversion to `tierAvg`:
```typescript
const invertedTierAvg = tierAvg?.map((v, i) =>
  INVERTED_DIMS.has(DIMENSIONS[i].key) ? 100 - v : v
);
```
Then use `invertedTierAvg` instead of raw `tierAvg`.

### H03. Consensus math pool denominator is structurally wrong

**File:** `pipeline/agent3_consensus.py` (lines 46-52)  
**Spec violation:** REQ-022 ("Consensus baseline computed over Tier 1 and Tier 2 sources")

```python
pool = [s for s in all_sources if s["tier"] in (1, 2) and s.get("active", 1)]
pool_size = len(pool)
# ...
pct = compute_baseline_pct(reporting, pool_size)  # reporting / pool_size * 100
```

The denominator is **all active tier 1+2 sources** (10 sources by default). A claim about German railway policy will not be reported by AP, ProPublica, or NPR — not because they disagree, but because it's outside their coverage scope. With only 2 of 10 sources reporting, the baseline is 20% — well below any threshold. Every niche-coverage claim stays `PENDING` forever.

The spec says "A claim enters the consensus baseline when it appears in more than threshold% of the pool's source graphs for that story" — the denominator should be "sources that covered this story" not "all tier 1/2 sources."

**Fix:** Two options (pick one):
- **(a)** Denominator = number of tier 1+2 sources that have at least one claim in this cluster. This measures agreement among sources that actually covered the story.
- **(b)** Use a minimum-reporting threshold (e.g., report must appear in at least 3 of the pool) before applying the percentage threshold.

### H04. 4 of 20 sources use Google News redirect URLs

**File:** `pipeline/scraper.py` (lines 6, 17, 21, 48-51)

Reuters, AP, NHK World, and Global Times use Google News RSS:
```python
"reuters": {"url": "https://news.google.com/rss/search?q=site:reuters.com...", "type": "google_news", ...}
```

Google News RSS entries return redirect URLs like `https://news.google.com/articles/CAIi...`. When passed to `newspaper4k` for extraction, these either fail to download or return the Google News wrapper page instead of the actual article. Additionally, these proxy URLs break the `UNIQUE` constraint on `articles.url` — the same article could have different redirect URLs across polls.

The scraper code acknowledges this at `_normalize()` line 50: `body_status = "BODY_UNAVAILABLE" if cfg["type"] == "google_news" else "AVAILABLE"` — but setting body status to unavailable doesn't fix the broken URLs stored in the database.

**Fix:** Either find native RSS feeds for these sources (Reuters has `https://www.reuters.com/tools/rss`, AP has `https://feeds.ap.org/`), or use the Google News RSS but extract the actual article URL from the redirect chain (follow the redirect before storing).

### H05. Sources page vertical filter has no effect on displayed data

**File:** `src/pages/Sources.tsx` (lines 28-53)
**Spec violation:** REQ-054, REQ-055, REQ-056 (vertical support implied — switching verticals should show different scores)

```typescript
const [vertical, setVertical] = useState<VerticalThresholdKey>("geopolitics");
// ...
const scoreMap = useMemo(
  () => new Map(scores.map((s) => [s.sourceId, s])),  // ALL scores, unfiltered
  [scores],
);
```

The `vertical` state is set via `VerticalPills` UI and shown in the subtitle ("Geopolitics vertical"), but never used to filter the `scores` array. If the parent passes scores for multiple verticals with the same `sourceId`, only the last one survives (Map key collision). Clicking "Economics" or "Technology" changes the subtitle text but the chart and ledger still show the same data.

**Fix:** Filter `scores` by the selected vertical before building `scoreMap`:
```typescript
const scoreMap = useMemo(
  () => new Map(
    scores.filter((s) => s.vertical === vertical).map((s) => [s.sourceId, s])
  ),
  [scores, vertical],
);
```
Note: This requires that `ReputationScore` includes a `vertical` field (check `src/data/scores.ts`).

---

## 🟡 MEDIUM

### M01. Theme/font-scale subscription races with Zustand persist hydration

**File:** `src/main.tsx` (lines 17-25)

```typescript
document.documentElement.classList.toggle(
  "dark",
  useStore.getState().theme === "dark",  // pre-hydration default
);
```

Zustand v5's `persist` middleware rehydrates asynchronously. At module eval time, `useStore.getState().theme` returns the default (`"dark"`), not the persisted value from localStorage. If the user set `light` theme, the page flashes dark before the subscription fires with the rehydrated value.

**Fix:** Either (a) use a synchronous rehydration strategy (`skipHydration` + manual rehydration), or (b) read from `localStorage` directly before the store subscription is established.

### M02. Onboarding dialog appears on every refresh

**File:** `src/components/AppNav.tsx` (lines 21-23)

```typescript
const onboardingComplete = useStore((s) => s.onboardingComplete);
const [dialogOpen, setDialogOpen] = useState(!onboardingComplete);
```

Same hydration race. `useState(!onboardingComplete)` during the first render evaluates with the default `false` (not hydrated), so `!false = true` → dialog opens. After hydration, `onboardingComplete` is `true`, but `useState` ignores the new value. The dialog appears on every refresh even after the user dismissed it.

**Fix:** Initialize `dialogOpen` to `false` and derive from the store directly inside the component render, or check localStorage directly for the initial state.

### M03. Zero delta renders empty string instead of "0"

**File:** `src/pages/SourceProfile.tsx` (line 233)

```typescript
{Math.abs(Math.round(diff!)) || ""}
```

`Math.round(0)` is `0`, which is falsy. `0 || ""` renders empty string. A source whose score changed by 0.4 points (rounded to 0) shows `▲` with no number, while a source that changed by 0.6 points shows `▲1`. The "flat" state uses `·`, but a tiny delta renders identically — no way to distinguish between truly flat and a rounded-to-zero change.

**Fix:** `{diff != null ? Math.abs(Math.round(diff!)).toString() : ""}` — always convert to string.

### M04. ScatterPlot D3 chart never redraws on container resize

**File:** `src/components/ScatterPlot.tsx` (lines 57-62, 64-205)

A `ResizeObserver` calls `setSize` on resize, triggering a React re-render. But the D3 rendering `useEffect` does not include `setSize` in its dependency array — `[data, hoveredId, onHover, onSelect]`. The chart renders once at initial dimensions and stays frozen. The `setSize` state variable causes pointless re-renders that achieve nothing.

**Fix:** Either include `setSize` in the dependency array, or use a ref to track the container's dimensions and compare them inside the effect using a ResizeObserver.

### M05. Consensus agent `_days_since` crashes on null/malformed dates

**File:** `pipeline/agent3_consensus.py` (lines 60-64)

```python
def _days_since(date_str: str | None) -> int:
    if not date_str:
        return 0       # ← correct guard for None
    dt = datetime.fromisoformat(date_str)  # ← crashes on RFC 2822
    now = datetime.now(timezone.utc)
    return (now - dt).days
```

The `None` guard is correct. But the function has no handling for non-ISO format dates (see C05 — same root cause, different crash path). Also, malformed date strings will raise `ValueError`.

**Fix:** Wrap in try/except, combine with C05's fix to ensure all stored dates are ISO format.

### M06. `ArticleExtractor` catches `Exception` (broader than intended)

**File:** `pipeline/extractor.py` (lines 14-17)

```python
except (ArticleException, Exception):
    return "", "BODY_UNAVAILABLE"
```

`ArticleException` is a subclass of `Exception`, so the tuple is redundant. This catches `KeyboardInterrupt`, `SystemExit`, `MemoryError`, and `GeneratorExit` — none of which should be silently swallowed as "body unavailable."

**Fix:** `except (ArticleException, OSError, ValueError):` — only catch exceptions that are realistic outcomes of article extraction.

### M07. Tier-to-symbol mapping duplicated in two places

**File:** `src/components/ScatterPlot.tsx` (lines 32-38) and `src/utils/shapes.ts` (lines 6-13)

Two independent mappings of tier → shape. If someone adds tier 6 to `shapes.ts` but forgets `ScatterPlot.tsx`, or changes a symbol name in one place but not the other, the shapes silently diverge. The D3 symbols aren't even imported from `shapes.ts` — ScatterPlot ignores the `getShapeForTier()` utility entirely.

**Fix:** Centralize in `shapes.ts` — export `TIER_D3_SYMBOLS` (mapping number → d3.SymbolType) alongside the existing string-based mapping, and use it in ScatterPlot.

### M08. Sparkline closest-snapshot reducer is redundant and less precise

**File:** `src/pages/SourceProfile.tsx` (lines 350-353)

The `SparklineGrid` component runs its own O(n) reduce to find the closest snapshot to `currentDay`, discarding the interpolation precision that `nearestSnapshots` + `interpolate` already computed. The displayed value in the sparkline labels can show raw snapshot values inconsistent with the StatPanel and Radar chart, which use the interpolated `currentSnapshot`.

**Fix:** Pass `currentSnapshot` directly to `SparklineGrid` rather than re-computing a closest-snapshot approximation.

### M09. Every API route creates a separate schema-loading connection

**File:** `app/main.py` (all routes), `db/connection.py` (line 13)

Schema is loaded on every connection (and fixed by overcoming C02, it would still run `executescript` on every request). Under concurrent load, this serializes on the schema's lock despite WAL mode (WAL only helps readers vs writers; writers still block writers).

**Fix:** Load schema once at application startup (in the lifespan context), not per-connection. Create a connection pool or reuse a single connection.

### M10. Schema load in `connection.py` uses `executescript` — not safe for concurrent use

**File:** `db/connection.py` (lines 11-13)

```python
def load_schema(conn: sqlite3.Connection) -> None:
    schema_sql = SCHEMA_PATH.read_text()
    conn.executescript(schema_sql)
```

`executescript` implicitly runs `BEGIN; <all statements>; COMMIT;` in one transaction. If two requests create connections simultaneously, one will block on the schema-level lock. Combined with WAL mode, this adds unnecessary serialization per request — for an operation that should happen once at startup.

### ~~M11. `compute_baseline_pct` has no guard against empty pool~~ **INCORRECT FINDING**

**Retracted.** The guard `if pool_size == 0: return 0.0` already exists at `pipeline/consensus.py` line 10-11. Verified by reading the file.

---

## 🔵 LOW

### L01. Dead exports and unused imports

- `src/utils/format.ts` line 3: `formatDecimalAsPercent` — defined, exported, never called anywhere (`grep -r "formatDecimalAsPercent" src/` returns only the definition)
- `app/test_routes.py` line 7: `from db.sources import insert_source` — imported, never used
- `db/claims.py` lines 3-4: `VALID_STATES` and `VALID_CONVERGENCE_TYPES` defined but never used in `update_claim_state`

### L02. Hardcoded sample IDs in navigation

**File:** `src/components/AppNav.tsx` (lines 13-19)

```typescript
{ to: "/source/reuters.com", label: "Source Profile" },
{ to: "/cluster/abc123", label: "Cluster Report" },
{ to: "/timeline/abc123", label: "Timeline" },
```

Clicking "Source Profile" always goes to Reuters. If you're viewing The Intercept, clicking nav takes you to Reuters. The Cluster Report and Timeline links always go to `abc123`. These are placeholder links that become confusing when the user is already on a source profile or cluster page.

### L03. `color-mix()` has no CSS fallback

**File:** `src/components/ArchetypePills.tsx` (lines 47-53)

```css
background-color: `color-mix(in srgb, ${TOKEN[pill.value]} 10%, transparent)`
```

`color-mix()` is supported in Chrome 111+, Firefox 113+, Safari 16.2+. On older browsers or embedded webviews, it fails silently and the entire `backgroundColor` resolves to `transparent` — the active pill has no visible background.

### L04. Store subscription in main.tsx never unsubscribed

**File:** `src/main.tsx` (line 20)

`useStore.subscribe()` returns an unsubscribe function. It's never saved or called. On Vite HMR cycles, this accumulates duplicate subscriptions. Not a production crash, but leaks on every hot reload.

### L05. 3 region labels defined with zero sources

**File:** `src/data/sources.ts` (lines 164-170)

Regions `africa`, `latam`, and `sa` have zero sources but appear in the Panel page geographic breakdown as empty progress bars with `width: 4%` (due to `Math.max(pct, 4)` on line 117). They take up visual space while showing zero count.

### L06. `update_claim_state` doesn't validate against `VALID_STATES`

**File:** `db/claims.py` (lines 3-4, 70-85)

`VALID_STATES` and `VALID_CONVERGENCE_TYPES` are defined but never used. A buggy caller passing an invalid state gets a hard-to-debug `sqlite3.IntegrityError` instead of a clear Python `ValueError`. Misspelling `"CONSENSUS_ABSORBED"` as `"CONSENSUS_ABSORBEDD"` silently inserts bad data.

---

## 🧪 TEST QUALITY

### T01. Scheduler thread leak — no shutdown in tests

**File:** `pipeline/test_scheduler.py` (lines 10-18), `app/test_routes.py` (lines 81-87)

`ScraperScheduler.start()` spawns a `BackgroundScheduler` (non-daemon thread). Tests call `start()` and `stop()` but never `shutdown()`. The `stop()` method (`scheduler.py` line 52-55) only calls `scheduler.remove_job("scrape")` — it does not call `scheduler.shutdown()`. The thread remains alive. APScheduler's `BackgroundScheduler` runs non-daemon threads by default, which can prevent process exit.

**Fix:** Either call `shutdown()` in test cleanup, or make the scheduler daemon:
```python
self._scheduler = BackgroundScheduler(daemon=True)
```

### T02. Test asserts against wrong database

**File:** `pipeline/test_scheduler.py` (lines 26-30)

```python
def test_run_once_inserts_articles(self, db):
    s = ScraperScheduler(":memory:")  # own in-memory DB
    s.run_once()
    articles = list_articles(db)       # fixture's in-memory DB (different!)
    assert len(articles) > 0
```

Each `:memory:` SQLite connection is completely independent. `ScraperScheduler(":memory:")` creates its own in-memory database, and the `db` fixture creates another. The test asserts against the fixture's database, but articles were inserted into the scheduler's private database. This test passes only if it's skipped (`@pytest.mark.network`) or if no one runs it — it doesn't test what it claims.

### T03. No-op test with zero assertions

**File:** `src/__tests__/router-shell.test.tsx` (lines 107-110)

```typescript
it("shows NotFound page for unknown routes", () => {
    // The catch-all route ... is covered by the npm run build gate.
});
```

Empty test body. Zero assertions. Passes by definition.

### T04. Network-dependent tests with no timeout

**File:** `pipeline/test_scraper.py` (lines 27-40), `pipeline/test_extractor.py` (lines 16-31)

Five tests hit live RSS feeds with no timeout configured. They depend on:
- DNS resolving correctly
- Rate limits not being hit
- RSS feed structure not changing
- Specific article behavior assumptions (NYT always paywalled, Guardian first entry always has 100+ chars)

These tests are inherently flaky. They should have explicit timeouts and be clearly tagged as integration tests.

### T05. Stub tests verify stub behavior (tautological)

**File:** `pipeline/test_agents.py` (lines 25-105, 107-122)

All agent `run()` tests and `WorkerClient` tests verify only that stubs return their hardcoded default values. `test_embed_stub_returns_zeros` explicitly admits in its name that it tests a stub. `IntakeClusteringAgent.run()` returning `[]` is tested — but there's no actual clustering logic to verify.

### T06. Untested TypeScript archetype utility

**File:** `src/utils/archetype.ts`

The Python backend version (`pipeline/archetype.py`) has 5 test cases in `pipeline/test_archetype.py`. The TypeScript frontend version is completely untested — no test file covers `src/utils/archetype.ts`. The comment in `pipeline/archetype.py` says "Matches the TypeScript implementation exactly" but only one side is tested.

---

## SPEC VIOLATIONS SUMMARY

| Requirement | Status | Finding | Impact |
|---|---|---|---|
| REQ-118 (Investigate: extracted claims) | **FAIL** | C03 — query never processed, claims never extracted | Feature non-functional |
| REQ-119 (Investigate: cross-source matches) | **FAIL** | C03 — no results produced | Feature non-functional |
| REQ-120 (Investigate: localStorage persistence) | **FAIL** | C03 — no results to persist | Feature non-functional |
| REQ-122 (Investigate: pipeline stages 1-3) | **FAIL** | C03 — no backend call made | Feature non-functional |
| REQ-082 (Polarity color by dimension) | **VIOLATED** | H01 — inverted dimensions colored opposite | Misleading UI |
| REQ-022 (Consensus baseline over T1+T2) | **VIOLATED** | H03 — denominator structurally wrong for niche claims | All niche claims stuck PENDING |
| REQ-046 (Daily snapshots) | **PARTIAL** | Schema + CRUD exist, but `write_daily_snapshots` call site unclear | Data pipeline gap |
| REQ-025 (Configurable thresholds) | **PASS** | Settings UI works, store persists | ✅ |
| REQ-004 (Footer tagline every page) | **PASS** | `PageShell.tsx` line 18 | ✅ |
| REQ-090 (Investigate snapshot banner) | **PASS** | `Investigate.tsx` lines 46-52 | ✅ |
| REQ-091 (Panel source activation) | **PASS** | `Panel.tsx` with Switch toggles | ✅ |

---

## WHY-IT-HAPPENED: Root Cause Analysis

### C01 — API routes query in-memory DB instead of persistent file

**Root cause: COMPOUNDING (WRONG-IMPL × OVERSIGHT)**

Two independent decisions combined to create this bug:

1. **Slice 8a plan (Decision 1):** The `get_db()` function was given `:memory:` as its default parameter, designed for the test pattern (in-memory DB per test, loaded from schema.sql). This is documented in the 8a plan's test strategy: "All backend tests use `pytest` with an in-memory SQLite database loaded from `db/schema.sql`."

2. **Slice 8a scaffold routes:** The route handlers called `get_db()` with no arguments, inheriting the `:memory:` default. The plan's Decision 3 says routes should "return empty structures, not 404" — they do return empty lists, but from the wrong database.

The lifespan context (`app/main.py` line 19) correctly reads `NN_DB_PATH` from env and passes it to `ScraperScheduler`, but no mechanism was created to share that path with the route handlers. The routes don't have access to `request.app.state.db_path` because it was never stored there — only `request.app.state.scraper` was set. Each route independently re-created its own connection to `:memory:`.

The design doc is clear that data should be persistent (Section 8: "SQLite database — App server volume") but doesn't specify the connection management architecture. The 8a plan doesn't mention how routes should access the database — it assumes the scaffold routes returning empty lists are sufficient for the slice's goals.

**Evidence in plan docs:** `docs/plan/008a-backend-scaffold.md` — Decision 3 ("Routes return empty structures, not 404") and test strategy ("All backend tests use in-memory SQLite"). The production path was never verified.

### C02 — Schema crash on 2nd request (CREATE TABLE without IF NOT EXISTS)

**Root cause: COMPOUNDING (WRONG-IMPL × OVERSIGHT)**

Three factors:

1. **Slice 8a architecture:** Schema is loaded on every `get_db()` call (connection.py lines 11-13). The plan says "load_schema(conn)" in every connection. This is fine for the test pattern (in-memory, fresh DB each time) but wasteful and dangerous for production (persistent file).

2. **Developer inconsistency:** The index at `schema.sql` line 30 uses `IF NOT EXISTS`, proving the developer knew the pattern. But none of the 6 `CREATE TABLE` statements use it. This is a simple oversight — the developer was in "build the schema" mode when writing the tables and "make it idempotent" mode when writing the index.

3. **No production-path testing:** The Slice 8a plan's verification checklist includes `pytest` and `uvicorn start` but doesn't include hitting a route twice to verify idempotent startup. The first request succeeds (schema is loaded onto an empty file), the second crashes (tables already exist).

**Evidence in plan docs:** `docs/plan/008a-backend-scaffold.md` — Decision 1 says "Schema loader runs on every connection." This architectural decision was correct for testing but incorrect for production, and no production-path verification was written to catch the issue.

### C03 — Investigate query silently discarded

**Root cause: WRONG-IMPL (implementation didn't follow plan)**

The Slice 7 plan explicitly specifies the correct behavior:

- Search form design (line "On submit"): "creates an empty `AdHocResult` with the query and no claims"
- Test strategy table: "Submitting stores query — Query appears in results after clicking submit"

But the implemented `handleSubmit()` (Investigate.tsx lines 32-39) only shows a transient "Submitted" message and clears the input — it never calls `addAdHocResult()`. The test at `investigate.test.tsx` line 66 was then written to match the broken implementation and given a comment that normalizes the bug: "does NOT store empty result on submit — shows transient status instead."

The plan says the results should be an "honest empty state" — store the query text even without claims. The implementation chose a less useful "transient message + discard" pattern instead. The UX text ("Pipeline analysis will populate results when the backend runs stages 1–3") further normalizes the non-functional state.

This is NOT a design gap — the design doc clearly defines what the page should do (REQ-118 through REQ-122), and the Slice 7 plan translates it into precise implementation details. The developer simply didn't wire the submit handler to the store.

**Evidence in plan docs:** `docs/plan/007-investigate-notfound.md` — Search form section explicitly says "creates an empty `AdHocResult` with the query and no claims." The test was written to match the buggy implementation, not the plan.

### C04 — Datetime subtraction crash (naive vs aware)

**Root cause: WRONG-IMPL (Python timezone gotcha)**

Standard Python pitfall. The `_days_since()` function in `agent3_consensus.py` (lines 62-63) calls `datetime.fromisoformat()` on a stored date string — which returns a **naive** datetime — then subtracts `datetime.now(timezone.utc)` — which returns a **timezone-aware** datetime. Python raises `TypeError: can't subtract offset-naive and offset-aware datetimes`.

The design doc doesn't mention timezone handling (reasonable — it's a section 3/4 detail about the analytical model, not Python implementation). The 8c plan doesn't address timezone awareness in the `_days_since` function.

`datetime.fromisoformat()` in Python 3.11 does NOT parse the timezone suffix "Z" correctly (fixed in 3.11+ only for `datetime.fromisoformat`, but SQLite's `datetime('now')` produces no timezone info at all). The developer used `datetime.now(timezone.utc)` (correctly) but parsed with the wrong counterpart.

**Evidence in plan docs:** `docs/plan/008c-consensus-engine.md` — Section "Decision 2" details the resolution state machine but doesn't specify timezone handling in date math.

### C05 — RSS dates in RFC 2822 crash `fromisoformat`

**Root cause: COMPOUNDING (OVERSIGHT × OVERSIGHT)**

Two independent oversights in two different files:

1. **`scraper.py` line 53:** The scraper stores `entry.get("published", "")` — feedparser's `published` field returns RFC 2822 strings like `"Mon, 15 Jan 2024 10:30:00 GMT"`. The plan's assumption validation (#2) verified that feeds return entries but did not verify the date format. Feedparser also provides `entry.published_parsed` (a `time.struct_time`), which is more reliable and format-agnostic — the developer didn't use it.

2. **`agent3_consensus.py` line 61:** The `_days_since()` function calls `datetime.fromisoformat()` on the stored date string, assuming all dates are ISO 8601. `fromisoformat()` cannot parse RFC 2822.

The 8b plan verified feed availability ("Assumption #2: RSS feed availability ✅") but not the date format of returned entries. The "assumption validation" process checked that feeds returned entries with URLs and body availability status, but didn't look at date format.

**Evidence in plan docs:** `docs/plan/008b-scraper-scheduler.md` — Assumption #2 details feed availability and URL types but is silent on date format.

### H01 — Polarity colors inverted for R_speed/R_frame/R_edit

**Root cause: DESIGN-GAP (polarity function lacked dimension context)**

The design doc clearly labels polarity for each dimension (§4 Reputation Dimensions table):
- R_speed: "Graded — low is favorable"
- R_frame: "Graded — low stddev is favorable"
- R_edit: "Graded — low is favorable"

But REQ-082 (the spec requirement) simply says "Polarity binding must assign color by dimension using getPolarityColor." The requirement specifies the *function name* but doesn't specify *how* polarity should vary per dimension. This created a gap: the function was written as a simple threshold-based colorizer (high=teal, low=red) with only one special case (trait dimensions get neutral color).

Meanwhile, `SourceProfile.tsx` defines `INVERTED_DIMS = new Set(["R_speed", "R_frame", "R_edit"])` in the same file (line 45) — but this knowledge only flowed into the radar chart (via `toRadarValues`), not into the `StatPanel`'s color call on line 218.

The polarity knowledge (which dimensions are inverted) and the color function live in separate files with no shared contract. The design doc describes the concept but doesn't prescribe an architecture for binding it to the code, and REQ-082 was written vaguely enough that the generic implementation passes a literal reading.

**Evidence in plan docs:** `docs/plan/008c-consensus-engine.md` — Assumption #3 says "polarity is a frontend render concern, not calculation." This is correct, but it also means no plan slice addressed how the frontend should handle it.

### H02 — Tier average not polarity-inverted on radar chart

**Root cause: OVERSIGHT (third dataset missed during inversion work)**

The `toRadarValues` helper correctly inverts `INVERTED_DIMS` for the current snapshot data (lines 267-272). The Day 0 baseline dataset also correctly uses `toRadarValues(baseline)` (line 306). But when `tierAvg` was added as a third dataset (lines 305-308), it was passed directly without inversion. This is the same file, same function — the developer simply forgot to apply the same treatment to the third argument.

This was likely a sequential implementation: first the current data (inverted correctly), then the baseline (passes through same helper, inverted correctly), then tierAvg (added later, missed). Not a design gap — purely an implementation oversight.

### H03 — Consensus denominator = all T1+T2 sources, blocking niche claims

**Root cause: DESIGN-GAP (ambiguous spec language + deliberate interpretation)**

The design doc says (§4): "The consensus baseline is computed over Tier 1+2 sources only (the consensus pool). A claim enters the consensus baseline when it appears in more than `threshold`% of the pool's source graphs for that story."

The phrase "for that story" is ambiguous — it could mean:
- **(A)** "% of all T1+T2 source graphs examining this story" = % of the total pool
- **(B)** "% of the T1+T2 source graphs **that covered** this story" = reporting subset

The Slice 8c plan (Decision 6) explicitly adopts interpretation A: "count how many distinct Tier 1+2 sources have reported any claim in this cluster. If ≥ threshold% of the Tier 1+2 pool, the cluster has a consensus baseline. Individual claims enter the baseline when ≥ threshold% of Tier 1+2 sources have reported that specific claim."

Interpretation A means a claim appearing in 2 of 10 T1+T2 sources = 20% baseline, regardless of whether the other 8 sources cover different beats. A German railway policy claim will never reach 65% consensus because only 4 of 10 T1+T2 sources might have a German bureau. The design doc should have specified whether the denominator is "sources that covered the story" vs "all sources."

This is a design gap — the spec is ambiguous on a critical analytical detail, and the plan documented the (flawed) interpretation without further escalation.

**Evidence in plan docs:** `docs/plan/008c-consensus-engine.md` — Decision 6 explicitly adopts interpretation A. The assumption verification (#2) flagged R_frame/R_edit/R_correct as not computable, but did not flag the denominator issue for niche claims.

### H04 — Google News redirect URLs for 4 sources

**Root cause: KNOWN-TRADEOFF (documented compromise for RSS availability)**

The 8b plan explicitly documents this as a known limitation:

- Section "Assumptions validated" #2: "6 sources required alternative feeds (4 Google News RSS, 1 FeedBurner, 1 alternate native)"
- "Google News RSS (4): reuters, ap, nhk-world, global-times. These return opaque `news.google.com/rss/articles/...` URLs... Body extraction is not possible from these URLs — entries get `body_status = 'BODY_UNAVAILABLE'`."
- Decision 4: "scraper starts paused — controlled via API"

The plan tested Google News RSS and found it returns entries with correct metadata (source identification, title, published date) but opaque URLs. The developer chose to include these sources for metadata coverage (title, published date) rather than exclude them entirely.

However, the plan's assumption validation didn't fully trace the consequences: opaque URLs also break (a) the `UNIQUE` constraint on `articles.url` (same article gets different redirect URLs across polls) and (b) frontend links pointing to the article (clicking goes to a Google redirect, not the actual article). These downstream effects weren't evaluated.

**Evidence in plan docs:** `docs/plan/008b-scraper-scheduler.md` — Assumption #2 clearly documents the Google News RSS limitation. The scraper's `_normalize()` function sets `body_status = "BODY_UNAVAILABLE"` for Google News entries as a direct consequence of this documented tradeoff.

### H05 — Sources page vertical filter has no effect

**Root cause: OVERSIGHT (UI added before data plumbing)**

The `Sources.tsx` page has three relevant pieces:
1. `VerticalPills` UI component and `vertical` state (line 28) — added for UX
2. Subtitle text showing the selected vertical (line 42) — added for UX
3. `scoreMap` (line 43-45) — filters by sourceId only, not vertical

The developer built the UI for vertical selection (pills, subtitle) but never filtered the underlying data by the selected vertical. The `ReputationScore` interface (`src/data/scores.ts`) has a `vertical: string` field, so the data supports it. But the `scoreMap` was written before the vertical concept was added to the page, and the existing filter was never updated.

This is not a design gap — the spec requires three verticals (REQ-054/055/056) and the Sources page is the primary display for them. It's simply an incomplete implementation: the UI chrome was built but the data plumbing was forgotten.

### M01 — Theme/font-scale hydration race in main.tsx

**Root cause: WRONG-IMPL (didn't account for async persist)**

Zustand v5's `persist` middleware rehydrates asynchronously. The default state (`theme: "dark"`) is returned by `useStore.getState()` at module eval time before localStorage is read. The subscription fires only after hydration completes.

The fix is well-documented in Zustand's own FAQs and migration guides. The developer didn't consult the documentation for this specific timing consideration.

### M02 — Onboarding dialog hydration race

**Root cause: WRONG-IMPL (`useState` locks in pre-hydration value)**

Same root as M01 but worse: `useState` only evaluates its initializer once. When hydration completes and `onboardingComplete` changes to `true`, the component re-renders but `setDialogOpen` was already initialized to `true` from the pre-hydration default. The dialog is already open, and since no code closes it, it stays open.

### M03 — Zero delta renders empty string

**Root cause: OVERSIGHT (JavaScript falsiness)**

`Math.abs(Math.round(0))` is `0`, which is falsy in JavaScript. `0 || ""` evaluates to `""`. Standard JavaScript trap — the developer chose the `||` pattern for conciseness without considering the numeric zero case.

### M04 — ScatterPlot never redraws on resize

**Root cause: OVERSIGHT (ResizeObserver wired but dependency array not updated)**

The developer correctly added a `ResizeObserver` and `setSize` state to trigger re-renders when the container resizes. But the D3 rendering `useEffect`'s dependency array was not updated to include `setSize`. React's `useEffect` only re-runs when deps change; the `useState` re-render alone doesn't trigger the effect.

This looks like the ResizeObserver was added by one person (or one pass) and the effect deps were never updated to match. The `setSize` state variable causes pointless re-renders (the state changes → React re-renders → D3 still at old dimensions → nothing visible changes).

### M05 — `_days_since` crashes on malformed dates

**Root cause: COMPOUNDING (same as C04 + C05)**

This is the downstream consequence of C04 (timezone awareness) and C05 (date format mismatch). The `_days_since` function has no `try/except` around `datetime.fromisoformat()`, so any malformed date string or RFC 2822 date results in a `ValueError` crash.

### M06 — ArticleExtractor catches Exception too broadly

**Root cause: OVERSIGHT (redundant exception handling)**

`except (ArticleException, Exception)` is equivalent to `except Exception` because `ArticleException` extends `Exception`. The developer likely added `ArticleException` for clarity and `Exception` as a safety net, not realizing:
- They're redundant
- `Exception` catches `KeyboardInterrupt`, `SystemExit`, `MemoryError` — none should be silently swallowed

### M07 — Duplicated tier-to-shape mapping

**Root cause: OVERSIGHT (utility created after implementation, never refactored)**

`src/utils/shapes.ts` was created as a utility after `src/components/ScatterPlot.tsx` was already written with its own inline mapping. The ScatterPlot was never refactored to import from `shapes.ts`. Two independent sources of truth now exist.

### M08 — Redundant closest-snapshot reduce in SparklineGrid

**Root cause: OVERSIGHT (subcomponent re-computes what parent already computed)**

The `SparklineGrid` sub-component independently finds the closest snapshot to the current day using a `reduce`, while the parent `SourceProfilePage` already computes `currentSnapshot` (interpolated) via `nearestSnapshots` + `interpolate`. The sparkline value shows the raw closest snapshot instead of the interpolated value, creating potential inconsistencies with the StatPanel.

### M09 — Every route creates separate schema-loading connection

**Root cause: COMPOUNDING (C01 + C02 architecture)**

Same root as C01 and C02. The architectural pattern of calling `get_db()` per-route was established in Slice 8a as the connection management strategy. Combined with schema-on-every-connection (C02), this creates unnecessary serialization under concurrent load. Fixing C01 and C02 (single connection, schema-once-at-startup) resolves this automatically.

### M10 — Schema load uses executescript, not safe for concurrent

**Root cause: COMPOUNDING (same as M09)**

`executescript` implicitly wraps everything in a transaction. Two concurrent `get_db()` calls would serialize on this. With the schema-once-at-startup fix for C02, this becomes irrelevant.

### ~~M11 — `compute_baseline_pct` division by zero~~ **INCORRECT FINDING**

**Retracted.** The guard `if pool_size == 0: return 0.0` already exists at `pipeline/consensus.py` line 10-11. Verified by reading the file.

### T01 — Scheduler thread leak in tests

**Root cause: OVERSIGHT (no test teardown for scheduler threads)**

Tests call `start()` and `stop()` but never `shutdown()`. The `stop()` method only removes the APScheduler job — it doesn't call `scheduler.shutdown()`, leaving the BackgroundScheduler's non-daemon thread alive. The `shutdown()` method exists in `scheduler.py` (line 70) but is never called in test cleanup. APScheduler BackgroundScheduler creates non-daemon threads by default, which can prevent the test process from exiting cleanly.

### T02 — Test asserts against wrong database

**Root cause: WRONG-IMPL (two in-memory databases, wrong one asserted against)**

`test_run_once_inserts_articles` creates `ScraperScheduler(":memory:")` — the scheduler's own `:memory:` database. Then it asserts against `db` — a different `:memory:` database from the fixture. Each `sqlite3.connect(":memory:")` call creates an independent database. The test passes because it's marked `@pytest.mark.network` and typically skipped in CI, so no one noticed the assertion was checking the wrong database.

### T03 — No-op test with zero assertions

**Root cause: INCOMPLETE (placeholder test left in place)**

The `router-shell.test.tsx` test at line 107 has an empty body with a comment explaining the catch-all route is "covered by the npm run build gate." This is a placeholder that was never replaced with a real test. It was likely written during Slice 0 (Router Shell) and never completed.

### T04 — Network-dependent tests with no timeout

**Root cause: OVERSIGHT (no timeout on live-feed tests)**

The Slice 8b plan's test strategy includes "Live RSS tests hit real URLs (BBC, Guardian)" and marks them with `@pytest.mark.network`. But no timeout was configured. If BBC's RSS feed is slow to respond, the test hangs indefinitely. The fix is a simple `@pytest.mark.timeout(10)` or equivalent.

### T05 — Stub tests verify stub behavior

**Root cause: INCOMPLETE (scaffold tests never replaced)**

The Slice 8a plan (Decision 2) says: "Each agent is an abstract base class... the stub returns `[]` / `{}` — never `NotImplementedError` or `pass`." The tests verify that the stubs return their expected types. These were written as placeholder tests during Slice 8a's scaffold phase and were never replaced with real tests when the agents were implemented in Slice 8c.

### T06 — Untested TypeScript archetype utility

**Root cause: OVERSIGHT (frontend utility never tested)**

The Slice 8c plan implemented `pipeline/archetype.py` as a port of `src/utils/archetype.ts`, with 5 test cases. The TypeScript original was never tested. When the backend version was written and tested, no one went back to add tests for the frontend version.

---

## PATTERNS OBSERVED

Reviewing all 26 findings, several patterns emerge:

1. **Complex compound bugs (4 findings):** C01, C02, C04, H04 — the most severe bugs are not simple mistakes but compound failures: two individually harmless decisions combine into a production blocker. Schema-on-every-connection × no-IF-NOT-EXISTS = crash on 2nd request. RSS dates × `fromisoformat` = TypeError.

2. **Plan-to-implementation drift (1 finding):** C03 — the Slice 7 plan explicitly said to store the query, but the implementation discarded it, and the test was then written to normalize the broken behavior.

3. **Assumption validation blind spots (3 findings):** C05 (feed date format), H03 (consensus denominator for niche stories), H04 (downstream effects of Google News URLs on dedup/links) — each was either missed or only partially verified during assumptions validation.

4. **Standard gotchas (4 findings):** C04 (Python timezone), H05 (UI before data), M01/M02 (Zustand async persist), M03 (JS falsy zero) — well-documented language/framework pitfalls that any developer can hit.

5. **Leftover scaffold (3 findings):** T03 (empty test body), T05 (stub tests never replaced), T06 (untested frontend utility with tested backend port).

6. **Not spec violations — missing production paths (2 findings):** C01 and C02 aren't design gaps — the spec and design doc are clear. They're production-readiness gaps that weren't caught because the test suite only tests `:memory:` databases, not the persistent file path.

---

## Post-Review Actions (2026-06-26)

Based on the findings in this review, the following changes were made:

### Spec changes

- **REQ-022 tightened** (`spec/requirements.md`): The consensus baseline denominator is now specified as "Tier 1+2 sources that have at least one claim in the same cluster" rather than "all Tier 1+2 sources." Resolves the ambiguity that caused H03.

### Design doc changes

- **Data Format Contracts subsection added** to `docs/design-v1.2.md` §3 (System Architecture): Defines system-wide formats for dates (ISO 8601 UTC with frontend display in America/Los_Angeles), URLs (canonical, no Google redirects), numeric scales (0–100), and nullable fields. Prevents C04/C05 from recurring.

### Deferred items

- **Route DB access pattern** added to `docs/deferred.md`: Open question whether API routes accessing the persistent database path belongs in the spec or is purely an implementation detail — from C01/C02 discussion.

### Workflow process gaps documented

- **`docs/workflow-gaps-01.md`** written: Documents 6 gaps in the dev-workflow process where the gate chain failed to catch the bugs found in this review. Each gap is traced back to specific findings and includes proposed fixes for the workflow gates.

## Fix Status — 2026-06-26 (implementation session)

Fixes applied to all confirmed findings. 22 of 26 resolved. 4 deferred (known tradeoffs / scaffold / niche).

### Fixed (22/26)

| ID | Severity | Summary | Files changed |
|----|----------|---------|---------------|
| C01 | Critical | API routes query persistent DB via FastAPI `Depends` | `app/main.py`, `db/connection.py` |
| C02 | Critical | `CREATE TABLE IF NOT EXISTS` on all schema objects; schema loaded once at startup | `db/schema.sql`, `db/connection.py`, `app/main.py` |
| C03 | Critical | Investigate `handleSubmit` calls `addAdHocResult()` | `src/pages/Investigate.tsx`, `src/__tests__/investigate.test.tsx` |
| C04 | Critical | `_days_since` handles naive datetimes (`.replace(tzinfo=utc)`) | `pipeline/agent3_consensus.py` |
| C05 | Critical | Scraper uses `published_parsed` for ISO 8601 dates | `pipeline/scraper.py` |
| H01 | High | `getPolarityColor` inverts low-is-good dimensions; `INVERTED_DIMS` centralized | `src/utils/polarity.ts` |
| H02 | High | Tier average inverted on radar chart | `src/pages/SourceProfile.tsx` |
| H03 | High | Consensus denominator = T1+T2 sources covering this story, not all T1+T2 | `pipeline/agent3_consensus.py` |
| H05 | High | Sources page `scoreMap` filters by selected vertical | `src/pages/Sources.tsx` |
| M01 | Medium | Theme reads localStorage before Zustand rehydrates | `src/main.tsx` |
| M02 | Medium | Onboarding dialog opens via `useEffect` after hydration | `src/components/AppNav.tsx` |
| M03 | Medium | Zero delta renders "0" (`.toString()`) | `src/pages/SourceProfile.tsx` |
| M04 | Medium | D3 chart redraws on resize (`size` in useEffect deps) | `src/components/ScatterPlot.tsx` |
| M05 | Medium | `_days_since` catches `(ValueError, TypeError)` | `pipeline/agent3_consensus.py` (combined with C04) |
| M06 | Medium | `ArticleExtractor` catches `(ArticleException, OSError, ValueError)` | `pipeline/extractor.py` |
| M07 | Medium | Tier→D3 symbol mapping centralized in `shapes.ts`; ScatterPlot imports it | `src/utils/shapes.ts`, `src/components/ScatterPlot.tsx` |
| M08 | Medium | SparklineGrid uses parent's interpolated `currentSnapshot` | `src/pages/SourceProfile.tsx` |
| M09 | Medium | Auto-resolved by C01/C02 (schema loaded once at startup, not per-connection) | — |
| M10 | Medium | Auto-resolved by C01/C02 (`executescript` runs once at startup) | — |
| L01 | Low | Removed `formatDecimalAsPercent`, unused `insert_source` import | `src/utils/format.ts`, `app/test_routes.py` |
| L04 | Low | `useStore.subscribe` return captured; Vite HMR dispose added | `src/main.tsx` |
| L06 | Low | `update_claim_state` validates against `VALID_STATES` | `db/claims.py` |
| T01 | Test | `BackgroundScheduler(daemon=True)` | `pipeline/scheduler.py` |
| T02 | Test | Temp file used so scheduler and assertion share DB | `pipeline/test_scheduler.py` |
| T03 | Test | No-op test removed | `src/__tests__/router-shell.test.tsx` |

### Deferred (4/26)

| ID | Severity | Reason |
|----|----------|--------|
| H04 | High | KNOWN-TRADEOFF — 4 sources use Google News RSS with opaque redirect URLs. Needs native RSS feeds found for Reuters, AP, NHK World, Global Times. Scraper already marks these `BODY_UNAVAILABLE`. |
| L02 | Low | Hardcoded nav IDs (`/source/reuters.com`, `/cluster/abc123`) are placeholder links. Not a bug — stub pages by design. |
| L03 | Low | `color-mix()` no CSS fallback. Supported in Chrome 111+, Firefox 113+, Safari 16.2+. Only affects embedded webviews. |
| L05 | Low | 3 region labels (`africa`, `latam`, `sa`) have zero sources. Visual clutter with `min-width: 4%` bar. Cosmetic. |
| T04 | Test | Network tests lack timeouts. Already `@pytest.mark.network` — skipped in CI. |
| T05 | Test | Stub tests verify stub behavior. Deliberate scaffold — agents are placeholders until backend pipeline is operational. |
| T06 | Test | Untested TypeScript `archetype.ts`. Python backend tested (`pipeline/test_archetype.py`). TS version mirrors it. |

### Test results after fixes

- **vitest:** 135 passed, 4 skipped (Docker integration)
- **pytest:** 155 passed, 6 deselected (network)
- **tsc:** No errors
- **Total:** 290 passing tests

### Files modified (21 files)

`app/main.py`, `app/test_routes.py`, `db/claims.py`, `db/connection.py`, `db/schema.sql`, `pipeline/agent3_consensus.py`, `pipeline/extractor.py`, `pipeline/scraper.py`, `pipeline/scheduler.py`, `pipeline/test_scheduler.py`, `src/components/AppNav.tsx`, `src/components/ScatterPlot.tsx`, `src/main.tsx`, `src/pages/Investigate.tsx`, `src/pages/SourceProfile.tsx`, `src/pages/Sources.tsx`, `src/__tests__/investigate.test.tsx`, `src/__tests__/router-shell.test.tsx`, `src/utils/format.ts`, `src/utils/polarity.ts`, `src/utils/shapes.ts`

---

## Subsequent Reviews

- **Slice 009 adversarial review** (2026-06-26): Scraper controls + header status indicator. 10 findings, 9 fixed, 1 pre-existing deferred. See plan doc for details.
- **Slice 010 adversarial review** (2026-06-26): Agent 3 hardening + daily snapshots + pipeline orchestration. 10 findings, 4 critical/high fixed (T1+2 filter, idempotency), 6 deferred. See plan doc for details.
