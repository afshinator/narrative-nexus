#!/usr/bin/env python3
"""GEMMA-2B: Batch extraction over Venezuela cluster (61 articles) via Gemma 4 E4B completions endpoint."""
import json, os, re, sys, sqlite3, time, urllib.request, urllib.error

MDL = "accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx"
CLUSTER_ID = 924
MAX_BODY_CHARS = 6000
MAX_TOKENS = 2048
RETRY_DELAY = 90  # seconds for cold-start retry
BATCH_RESULTS = "docs/evidence/gemma/batch_results.json"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline.agent2_forensic import EXTRACTION_SYSTEM_PROMPT as SYS


def load_key():
    f = os.path.expanduser("~/.hermes/.env")
    with open(f) as fh:
        for ln in fh:
            if ln.strip().startswith("FIR") and not ln.strip().startswith("#"):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("FIREWORKS_API_KEY not found in ~/.hermes/.env")


def call_gemma(prompt, key):
    """Call Gemma completions endpoint. Returns (parsed_response, error_str)."""
    body_data = {
        "model": MDL,
        "prompt": prompt,
        "max_tokens": MAX_TOKENS,
        "stop": ["<end_of_turn>"],
    }
    body = json.dumps(body_data).encode()
    req = urllib.request.Request(
        "https://api.fireworks.ai/inference/v1/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        return None, f"HTTP {e.code}: {err_body[:300]}"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def parse_claims_from_text(text):
    """Extract JSON claims from Gemma output. Returns list or raises."""
    text = text.strip()
    # Find first JSON opening
    for i, ch in enumerate(text):
        if ch in "{[":
            text = text[i:]
            break
    opener = text[0]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_string = False
    escape = False
    end = 0
    for i, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == 0:
        raise ValueError(f"unbalanced JSON at depth {depth}")
    data = json.loads(text[:end])
    # Normalize to {"results": [...]}
    if isinstance(data, list):
        data = {"results": data}
    if "results" not in data:
        for alt in ("articles", "data", "output"):
            if alt in data and isinstance(data[alt], list):
                data = {"results": data[alt]}
                break
    if "results" not in data:
        for k in list(data.keys()):
            if isinstance(data[k], list):
                data = {"results": data[k]}
                break
    return data


def main():
    # Tee output to log file
    import __main__
    log_path = os.path.join(os.path.dirname(BATCH_RESULTS), "batch_run.log")
    log_fh = open(log_path, "w")
    _orig_print = __builtins__.print

    def tee_print(*args, **kwargs):
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        msg = " ".join(str(a) for a in args)
        line = f"[{ts}] {msg}"
        log_fh.write(line + "\n")
        log_fh.flush()
        _orig_print(*args, **kwargs)

    __builtins__.print = tee_print

    key = load_key()

    # B3: Read articles from golden DB (read-only)
    conn = sqlite3.connect("file:data/demo/demo.db?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT a.id, a.title, a.body, a.source_id, s.name as source_name
           FROM articles a
           JOIN claims cl ON cl.article_id = a.id
           JOIN sources s ON s.id = a.source_id
           WHERE cl.cluster_id = ?
             AND a.body IS NOT NULL
             AND length(a.body) > 200
           GROUP BY a.id
           ORDER BY a.id""",
        (CLUSTER_ID,),
    ).fetchall()
    conn.close()

    articles = [dict(r) for r in rows]
    print(f"B4: {len(articles)} articles in cluster {CLUSTER_ID}")
    print(f"Model: {MDL}")
    print(f"max_tokens: {MAX_TOKENS}, body cap: {MAX_BODY_CHARS}")
    print()

    os.makedirs(os.path.dirname(BATCH_RESULTS), exist_ok=True)

    all_results = []
    first_ten_errors = 0
    total_articles = len(articles)
    last_activity = time.time()

    for idx, art in enumerate(articles):
        art_id = art["id"]
        source = art["source_name"]
        body = art["body"] or ""
        truncated = len(body) > MAX_BODY_CHARS
        if truncated:
            body = body[:MAX_BODY_CHARS]
            trunc_note = " (truncated)"
        else:
            trunc_note = ""

        # Build prompt exactly like Agent 2: system prompt then article
        article_text = (
            f"\n--- ARTICLE {art_id} ---\n"
            f"{art['title'] or ''}\n"
            f"{body}\n"
        )
        prompt = f"<start_of_turn>user\n{SYS}\n\nArticles:{article_text}<end_of_turn>\n<start_of_turn>model\n"

        print(f"[{idx+1}/{total_articles}] article {art_id} ({source}){trunc_note}...", end=" ", flush=True)

        resp, err = call_gemma(prompt, key)

        # Cold-start retry (addendum)
        if err and ("DEPLOYMENT_SCALING_UP" in err or "503" in err or "timed out" in err.lower()):
            print(f"cold-start, waiting {RETRY_DELAY}s...", end=" ", flush=True)
            time.sleep(RETRY_DELAY)
            resp, err = call_gemma(prompt, key)

        if err:
            print(f"API ERROR: {err}")
            all_results.append(
                {
                    "article_id": art_id,
                    "source": source,
                    "n_claims": 0,
                    "claims": [],
                    "usage": {},
                    "parse_ok": False,
                    "error": err,
                }
            )
            if idx < 10:
                first_ten_errors += 1
        else:
            text = resp["choices"][0]["text"]
            usage = resp.get("usage", {})
            finish = resp["choices"][0].get("finish_reason", "?")
            if not text or not text.strip():
                print(f"EMPTY RESPONSE (finish={finish})")
                all_results.append(
                    {
                        "article_id": art_id,
                        "source": source,
                        "n_claims": 0,
                        "claims": [],
                        "usage": usage,
                        "parse_ok": False,
                        "error": f"Empty response text (finish={finish})",
                    }
                )
                continue
            try:
                parsed = parse_claims_from_text(text)
                results_list = parsed.get("results", [])
                # Sum all claims from all article entries in results
                claims = []
                for r in results_list:
                    if isinstance(r, dict):
                        claims.extend(r.get("claims", []))
                n_claims = len(claims)
                parse_ok = True
                print(f"{n_claims} claims (finish={finish})")
                all_results.append(
                    {
                        "article_id": art_id,
                        "source": source,
                        "n_claims": n_claims,
                        "claims": claims,
                        "usage": usage,
                        "parse_ok": True,
                        "finish_reason": finish,
                        "raw_text_len": len(text),
                    }
                )
            except (json.JSONDecodeError, ValueError, KeyError, AttributeError) as e:
                parse_ok = False
                print(f"PARSE FAIL: {e}")
                all_results.append(
                    {
                        "article_id": art_id,
                        "source": source,
                        "n_claims": 0,
                        "claims": [],
                        "usage": usage,
                        "parse_ok": False,
                        "error": f"Parse error: {e}",
                        "raw_text_preview": text[:500],
                    }
                )

        # Incremental save after each article
        with open(BATCH_RESULTS, "w") as f:
            json.dump(all_results, f, indent=2, default=str)

        last_activity = time.time()

    # STOP GATE: >50% of first 10 hard-fail (API errors)
    if first_ten_errors > 5:
        print(f"\nSTOP: {first_ten_errors}/10 API errors in first 10 articles")
        # Write partial results
        with open(BATCH_RESULTS, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"Partial results written to {BATCH_RESULTS}")
        sys.exit(0)

    # Summary
    total_claims = sum(r["n_claims"] for r in all_results)
    total_claims_alt = sum(len(r["claims"]) for r in all_results)
    parse_ok_count = sum(1 for r in all_results if r["parse_ok"])
    total_prompt_tokens = sum(r.get("usage", {}).get("prompt_tokens", 0) or 0 for r in all_results)
    total_completion_tokens = sum(r.get("usage", {}).get("completion_tokens", 0) or 0 for r in all_results)
    claim_counts = [r["n_claims"] for r in all_results if r["parse_ok"]]
    if claim_counts:
        claim_counts_sorted = sorted(claim_counts)
        n = len(claim_counts_sorted)
        median = claim_counts_sorted[n // 2] if n % 2 == 1 else (claim_counts_sorted[n // 2 - 1] + claim_counts_sorted[n // 2]) / 2
    else:
        median = 0

    print()
    print("=" * 50)
    print("BATCH SUMMARY")
    print(f"  Articles attempted:  {total_articles}")
    print(f"  Parse OK:            {parse_ok_count}")
    print(f"  Parse failures:      {total_articles - parse_ok_count}")
    print(f"  Total claims (sum):  {total_claims}")
    print(f"  Total claims (alt):  {total_claims_alt}")
    print(f"  Claims tie-out:      {'PASS' if total_claims == total_claims_alt else 'FAIL'}")
    if claim_counts:
        print(f"  Claim count min:     {min(claim_counts)}")
        print(f"  Claim count median:  {median}")
        print(f"  Claim count max:     {max(claim_counts)}")
    print(f"  Prompt tokens:       {total_prompt_tokens}")
    print(f"  Completion tokens:   {total_completion_tokens}")
    print(f"  Total tokens:        {total_prompt_tokens + total_completion_tokens}")
    print("=" * 50)

    # Write results
    with open(BATCH_RESULTS, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults written to {BATCH_RESULTS}")


if __name__ == "__main__":
    main()
