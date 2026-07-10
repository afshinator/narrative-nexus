#!/usr/bin/env python3
"""G4: Gemma extraction pass via COMPLETIONS endpoint."""
import json, os, re, sys, sqlite3, urllib.request

DBP = "/tmp/gemma-scratch.db"
AID = 6
MDL = "accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx"

def _key():
    f = os.path.expanduser("~/.hermes/.env")
    with open(f) as fh:
        for ln in fh:
            if ln.strip().startswith("FIR") and not ln.strip().startswith("#"):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("key not found")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline.agent2_forensic import EXTRACTION_SYSTEM_PROMPT as SYS

def _call(prompt, key):
    body = json.dumps({"model": MDL, "prompt": prompt, "max_tokens": 8000, "stop": ["<end_of_turn>"]}).encode()
    req = urllib.request.Request("https://api.fireworks.ai/inference/v1/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())

def _parse_json(text):
    """Extract first JSON from Gemma output, normalize to {"results": [...]}."""
    text = text.strip()
    for i, ch in enumerate(text):
        if ch in '{[':
            text = text[i:]
            break
    depth = 0
    in_string = False
    escape = False
    end = 0
    opener = text[0]
    closer = '}' if opener == '{' else ']'
    for i, ch in enumerate(text):
        if escape:
            escape = False; continue
        if ch == '\\':
            escape = True; continue
        if ch == '"':
            in_string = not in_string; continue
        if in_string: continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                end = i + 1; break
    if end == 0:
        raise ValueError("unbalanced JSON at depth " + str(depth))
    data = json.loads(text[:end])
    if isinstance(data, list):
        data = {"results": data}
    # Normalize top-level key
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
    key = _key()
    conn = sqlite3.connect(DBP)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id, title, body, source_id, published_at FROM articles WHERE id=?",
        (AID,)).fetchone()
    conn.close()
    art = dict(row)
    print(f"Article {AID}: {art['title']}")
    print(f"Body: {len(art['body'] or '')} chars, source_id={art['source_id']}")

    atxt = f"\n--- ARTICLE {art['id']} ---\n{art['title'] or ''}\n{(art['body'] or '')[:400]}\n"
    prompt = f"<start_of_turn>user\n{SYS}\n\nArticles:{atxt}<end_of_turn>\n<start_of_turn>model\n"
    print(f"Prompt: {len(prompt)} chars, calling Gemma...")

    resp = _call(prompt, key)
    text = resp["choices"][0]["text"]
    model_str = resp["model"]
    fp_str = resp.get("system_fingerprint", "?")
    usage_str = json.dumps(resp["usage"])
    finish = resp["choices"][0]["finish_reason"]
    print(f"\nModel: {model_str}")
    print(f"Fingerprint: {fp_str}")
    print(f"Usage: {usage_str}")
    print(f"Finish: {finish}")
    print(f"\n=== GEMMA RAW OUTPUT ===\n{text[:1500]}")
    if len(text) > 1500:
        print(f"... (truncated, total {len(text)} chars)")
    print("=== END RAW ===")

    data = _parse_json(text)
    results = data.get("results", [])
    print(f"\nParsed {len(results)} results")
    conn2 = sqlite3.connect(DBP)
    total_claims = 0
    for r in results:
        claims = r.get("claims", [])
        fs = r.get("framing_score")
        model_aid = r.get("article_id", "?")
        print(f"  article_id(model)={model_aid} framing_score={fs} claims={len(claims)}")
        for c in claims:
            print(f"    - {c.get('text','?')[:150]}")
        if fs is not None:
            conn2.execute(
                "INSERT OR IGNORE INTO article_framing (article_id, llm_score, lexical_score, sentiment_score) VALUES (?,?,0.0,0.0)",
                (AID, float(fs)))
        for c in claims:
            txt = c.get("text","")
            if not txt: continue
            cur = conn2.execute(
                "INSERT INTO claims (article_id, cluster_id, text, state, created_at) VALUES (?,0,?,'PENDING',?)",
                (AID, txt, art.get("published_at")))
            cid = cur.lastrowid
            conn2.execute(
                "INSERT INTO claim_sources (claim_id, source_id, first_seen_at) VALUES (?,?,?)",
                (cid, art["source_id"], art.get("published_at")))
            total_claims += 1
    conn2.commit()
    conn2.close()
    print(f"\nDB: {total_claims} claims committed to {DBP}")
    if results:
        r0 = results[0]
        print(f"Note: model returned article_id={r0.get('article_id','?')}, overridden to actual {AID}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
