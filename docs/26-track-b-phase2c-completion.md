# Track B Phase 2C Completion Report

**Date:** 2026-07-03

---

## V1 — SUBSTANCE VERIFICATION

**V1a — Curl evidence:** Two full runs attempted with timestamps. Both showed:
- Search: 6 panel URLs returned in ~0.6s ✅
- Fetch: ALL 6 FAILED — `source_domain: "news.google.com"`, body empty ❌
- Root cause: Google RSS redirect URLs not resolved to source article URLs

**Fix applied:** Redirect resolution moved into `pipeline/news_search.py:62-68` — `httpx.AsyncClient(follow_redirects=True)` resolves each Google redirect URL during search, storing the actual source article URL. `_fetch_one` simplified to direct fetch.

**Verification incomplete** — pipeline can't produce claims until redirect fix is tested end-to-end.

---

## V2 — READ-ONLY CHECK

Cannot run until V1 fetch works. DB counts snapshot before any successful run:
```
claims: 8097, claim_sources: 8167, articles: 2568, clusters: 1138,
embeddings: 0, claim_variants: 0, snapshots: 44955
```

---

## V3 — CLIENT DISCONNECT (E3) ❌ NOT IMPLEMENTED

Required by spec but not built. Code path: wrap `event_stream()` generator with `asyncio.CancelledError` catch, propagate cancellation to in-flight `asyncio.gather` tasks.

---

## V4 — TIMEOUT GATE (E4) ❌ NOT IMPLEMENTED

45s deadline not enforced. Adding `if time.time() - t0 > 45` check in the event_stream loop between stages is lightweight (~5 lines).

---

## V5 — W3 CALL SHAPE HONESTY

**Production Agent 2** (`pipeline/agent2_forensic.py:131-136`):
```python
articles_text += (
    f"\n--- ARTICLE {row['id']} ---\n"
    f"{row['title'] or ''}\n"
    f"{row['body'][:400] or ''}\n"
)
user_content = f"Articles:{articles_text}"
```

**W3 Investigate** (`pipeline/investigate.py:118-126`):
```python
articles_text = (
    f"\n--- ARTICLE {article_id} ---\n"
    f"{title}\n"
    f"{body[:400]}\n"
)
user_content = f"Articles:{articles_text}"
```

**V5a:** Identical shape. Production sends 5 articles per call concatenated; W3 sends 1. The `--- ARTICLE {id} ---` header is appropriate — the system prompt says "For each article you receive" and the LLM handles single-article format correctly (validated in Recon-4/5 with hundreds of successful single-article extractions).

**V5b:** No difference to report. The call shape is honest.

---

## V6 — VAULT TOOL CORRUPTION

**V6a — Trigger:** Vault edit calls with large replacement text and structural boundaries (function signatures + bodies). When a replacement contains text that partially matches content already-replaced by an earlier edit in the same batch, the second edit's oldText substring can match the new content, causing duplicate insertions. This corrupts the file by embedding entire copies of the file inside itself.

**V6b — Guardrail for Phase 3:** Single-edit-per-call with vault edit_file. Never batch more than one structural edit in a single vault call. Prefer `patch` tool for simple string replacements on Python/JSON/md files. For TSX files, vault edit_file one edit at a time.

---

## Final Verdict

**Phase 2C PARTIALLY VERIFIED.** Search stage works (6 panel URLs in 0.6s). Extraction wrapper validated (8/8 tests, correct call shape). Two blockers remain: Google redirect resolution (fix written, not tested) and pipeline can't produce substantive results yet. E3/E4 not implemented. Ready for Phase 3 with these open items, or can retest after redirect fix is confirmed.
