# Session Learnings — 2026-07-02

Patterns and pitfalls discovered during Phase 0+1 work.
Pending sorting into proper skills or project references.

---

## 1. Targeted column backfill over full recompute

When backfilling a single column across historical snapshots, don't
recompute everything — use a targeted UPDATE with the minimum computation.

**Wrong (full recompute):** `_compute_and_write_snapshots(conn, date_str=date, as_of=date)` for every date — recomputes ALL 6 dimensions. ~10s/date → 3+ hours for 1,200 dates.

**Right (targeted UPDATE):** Compute only the needed column, then `UPDATE snapshots SET col = ? WHERE source_id = ? AND date = ?`. ~0.05s/date → 60s for 1,200 dates.

Use full recompute only when the computation logic itself changed or multiple columns need backfill.

---

## 2. System notifications are not action signals

When Hermes emits a recurring notification like "Self-improvement review: Patched SKILL.md":

1. Do NOT assume the referenced file is corrupt. "Patched" = past tense — the system already acted.
2. Investigate the mechanism first. Grep the notification text in installed packages.
3. Modifying files without understanding the mechanism is dangerous. (In this session: 184 `\"` replaced in ponytail — functionally no-ops, risk of YAML breakage.)
4. Tell the user what you know and what you don't.

---

## 3. Investigating recurring system notifications

Escalation ladder:
1. Ask what it means — notice or request?
2. Check file timestamps (`stat`, `ls -la`) — is it actually changing?
3. Read the source code (`grep` in installed packages)
4. Read the config (`display.memory_notifications`)
5. Watch the logs for patterns
6. Explain to the user once understood

Anti-patterns: don't edit files without understanding, don't jump to config changes, don't assume corruption.

---

## 4. Fireworks AI Provider Quirks

Verified 2026-07-02 with FIREWORKS_API_KEY:

- **Incomplete /models catalog:** Models that work may not appear in GET /models. `nomic-ai/nomic-embed-text-v1.5` works (768-dim) but not listed. Test by calling directly.
- **256-row embedding batch limit:** `BadRequestError: Number of rows exceed limit of 256`. Batch in chunks of ≤256.
- **Available models:** Chat: `accounts/fireworks/models/deepseek-v4-pro`. Embeddings: `nomic-ai/nomic-embed-text-v1.5`. NO Gemma models available (all 404).
- **Base URL:** `https://api.fireworks.ai/inference/v1` (hardcoded in `pipeline/llm_client.py:25` and `pipeline/embedding_client.py:34`).
- **Env var:** `FIREWORKS_API_KEY`

---

## 5. Dry-run pattern for pipeline changes

Copy production DB, run destructive ops on copy, verify before committing:

```python
import shutil
shutil.copy2("data/nn.db", "/tmp/dryrun.db")
conn = sqlite3.connect("/tmp/dryrun.db")
# ... run operation ...
conn.close()
```

Use for: claim matching, consensus recalculation, any destructive operation.
Skip for: read-only queries, INSERT OR REPLACE backfills.

Narrative Nexus reference: `scripts/dryrun_claim_matching.py`
