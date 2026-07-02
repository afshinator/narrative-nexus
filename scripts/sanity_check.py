#!/usr/bin/env python3
"""Sanity-check suite for Narrative Nexus — run before any live demo.

Catches: proxy port mismatches, empty pages, missing dimensions, broken API endpoints,
         null data, stale config, build failures.

Usage:
  python3 scripts/sanity_check.py [--frontend http://localhost:3015] [--backend http://localhost:3006]
"""

import json
import os
import sys
import urllib.request
import urllib.error
from typing import Any

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0

def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}  —  {detail}" if detail else f"  ✗ {name}")


# ── Config ───────────────────────────────────────────────────────────────

BACKEND = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--backend" else "http://localhost:3006"
FRONTEND = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--frontend" else "http://localhost:3015"
# Handle both --backend and --frontend in either order
for i, arg in enumerate(sys.argv):
    if arg == "--backend" and i + 1 < len(sys.argv):
        BACKEND = sys.argv[i + 1]
    if arg == "--frontend" and i + 1 < len(sys.argv):
        FRONTEND = sys.argv[i + 1]


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def fetch_text(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except urllib.error.URLError:
        return 0, ""


# ══════════════════════════════════════════════════════════════════════════
# PHASE 0 — Environment & config (no server needed)
# ══════════════════════════════════════════════════════════════════════════

print("\n── Phase 0: Environment & Config ──")

# 0a. .env file exists and loads
try:
    from dotenv import load_dotenv
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, ".env")
    check(".env file exists", os.path.isfile(env_path), f"Expected at {env_path}")
    if os.path.isfile(env_path):
        load_dotenv(env_path)
        check(".env loads without error", True)
    else:
        check(".env loads without error", False, ".env missing")
except ImportError:
    check("python-dotenv installed", False, "pip install python-dotenv")

# 0b. Required API keys are set
for key in ("FIREWORKS_API_KEY", "DEEPSEEK_API_KEY"):
    val = os.environ.get(key, "")
    check(f"{key} is set", bool(val), f"Missing — add to .env or export")

# 0c. config/providers.json is valid
try:
    config_path = os.path.join(project_root, "config", "providers.json")
    with open(config_path) as f:
        cfg = json.load(f)
    defaults = cfg.get("defaults", {})
    for slot in ("agent1_llm", "agent2_llm", "agent4_llm"):
        provider_id = defaults.get(slot, "")
        check(f"config: {slot} defaults to '{provider_id}'",
              provider_id == "fireworks",
              f"Expected 'fireworks', got '{provider_id}'")
except Exception as e:
    check("config/providers.json loads", False, str(e)[:80])

# ══════════════════════════════════════════════════════════════════════════
# PHASE 1 — Backend API health
# ══════════════════════════════════════════════════════════════════════════

print("\n── Phase 1: Backend API ──")

# 1a. Health endpoint
try:
    data = fetch_json(f"{BACKEND}/api/health")
    check("GET /api/health returns 200", data.get("status") == "ok")
except Exception:
    check("GET /api/health returns 200", False, f"Backend at {BACKEND} unreachable — wrong port or not running")

# 1b. Sources
try:
    data = fetch_json(f"{BACKEND}/api/sources")
    sources = data.get("sources", [])
    check("GET /api/sources returns list", isinstance(sources, list) and len(sources) > 0,
          f"Got {len(sources) if isinstance(sources, list) else type(sources).__name__}")
    if sources:
        check("Sources have required fields",
              all(k in sources[0] for k in ("id", "name", "domain", "tier")),
              f"Missing fields. Have: {list(sources[0].keys())}")
except Exception as e:
    check("GET /api/sources works", False, str(e)[:80])

# 1c. Scores — critical: must have all 6 dimensions
try:
    data = fetch_json(f"{BACKEND}/api/scores")
    scores = data.get("scores", [])
    check("GET /api/scores returns list", len(scores) > 0, f"Got {len(scores)} sources")
    if scores:
        required_dims = {"R_orig", "R_val", "R_speed", "R_frame", "R_edit", "R_correct"}
        have = set(scores[0].keys())
        missing = required_dims - have
        check("All 6 radar dimensions present in /api/scores",
              not missing, f"Missing: {missing}")
        # Check non-null
        null_dims = [d for d in required_dims if scores[0].get(d) is None]
        check("Radar dimensions are non-null",
              not null_dims, f"NULL dimensions: {null_dims}")
except Exception as e:
    check("GET /api/scores works", False, str(e)[:80])

# 1d. Snapshots
try:
    data = fetch_json(f"{BACKEND}/api/snapshots")
    snaps = data.get("snapshots", [])
    check("GET /api/snapshots returns data", len(snaps) > 0, f"Got {len(snaps)} snapshots")
except Exception as e:
    check("GET /api/snapshots works", False, str(e)[:80])

# 1e. Clusters
try:
    data = fetch_json(f"{BACKEND}/api/clusters")
    clusters = data.get("clusters", [])
    check("GET /api/clusters returns data", isinstance(clusters, list),
          f"Got {type(clusters).__name__}")
except Exception as e:
    check("GET /api/clusters works", False, str(e)[:80])

# 1f. Provider config
try:
    data = fetch_json(f"{BACKEND}/api/config/providers")
    providers = data.get("providers", {})
    check("GET /api/config/providers returns OK",
          "providers" in data or "agent1_llm" in data,
          f"Keys: {list(data.keys())[:8]}")
except Exception as e:
    check("GET /api/config/providers works", False, str(e)[:80])


# ══════════════════════════════════════════════════════════════════════════
# PHASE 2 — Frontend proxy
# ══════════════════════════════════════════════════════════════════════════

print("\n── Phase 2: Frontend Proxy ──")

# 2a. Frontend serves HTML
try:
    status, html = fetch_text(FRONTEND)
    check("Frontend serves 200 HTML", status == 200 and "<!doctype html>" in html[:200].lower(),
          f"Status {status}" if status != 200 else "Not HTML")
except Exception as e:
    check("Frontend reachable", False, f"{FRONTEND} unreachable — wrong port or not running")

# 2b. Proxy: frontend can reach /api through Vite proxy
try:
    data = fetch_json(f"{FRONTEND}/api/health")
    check("Vite proxy: /api/health through frontend",
          data.get("status") == "ok",
          f"Got: {data}. Proxy likely pointed at wrong backend port.")
except Exception as e:
    check("Vite proxy: /api/health through frontend", False,
          f"Proxy broken: {str(e)[:80]}")

# 2c. Proxy: scores through frontend
try:
    data = fetch_json(f"{FRONTEND}/api/scores")
    scores = data.get("scores", [])
    check("Vite proxy: /api/scores through frontend",
          len(scores) > 0, f"Got {len(scores)} sources — proxy may be broken")
except Exception as e:
    check("Vite proxy: /api/scores through frontend", False, str(e)[:80])


# ══════════════════════════════════════════════════════════════════════════
# PHASE 3 — Data integrity
# ══════════════════════════════════════════════════════════════════════════

print("\n── Phase 3: Data Integrity ──")

try:
    data = fetch_json(f"{BACKEND}/api/scores")
    scores = data.get("scores", [])

    # 3a. No source has all-NULL dimensions
    all_null = []
    for s in scores:
        dims = [s.get(d) for d in ("R_orig", "R_val", "R_speed", "R_frame", "R_edit", "R_correct")]
        if all(v is None for v in dims):
            all_null.append(s.get("sourceId"))
    check("No source has all-NULL dimensions",
          len(all_null) == 0, f"Sources with all NULL: {all_null}")

    # 3b. Score ranges are 0-100
    out_of_range = []
    for s in scores:
        for d in ("R_orig", "R_val", "R_speed", "R_frame", "R_edit", "R_correct"):
            v = s.get(d)
            if v is not None and (v < 0 or v > 100):
                out_of_range.append(f"{s['sourceId']}.{d}={v}")
    check("All scores within 0-100 range",
          len(out_of_range) == 0, f"Out of range: {out_of_range[:5]}")

    # 3c. At least some variation (not all identical)
    frame_vals = [s["R_frame"] for s in scores if s.get("R_frame") is not None]
    if len(frame_vals) >= 3:
        check("R_frame has variation across sources",
              len(set(frame_vals)) > 1,
              f"All R_frame values = {frame_vals[0]} — likely uninitialized")

    # 3d. Profile endpoint: latest snapshot must have non-null dimensions
    try:
        data = fetch_json(f"{BACKEND}/api/sources/1/profile?vertical=geopolitics")
        snaps = data.get("snapshots", [])
        if snaps:
            latest = snaps[-1]
            null_dims = [d for d in ("R_orig","R_val","R_speed","R_frame","R_edit","R_correct")
                        if latest.get(d) is None]
            check("Profile endpoint returns non-null latest snapshot dimensions",
                  not null_dims,
                  f"NULL dimensions in latest snapshot: {null_dims}")
    except Exception:
        pass  # already covered by Phase 1
except Exception as e:
    check("Data integrity checks", False, str(e)[:80])


# ══════════════════════════════════════════════════════════════════════════
# PHASE 4 — Build artifact (optional, checks dist/ exists)
# ══════════════════════════════════════════════════════════════════════════

print("\n── Phase 4: Build ──")
import os

# 4a. dist/ exists (if running in production mode)
dist_path = os.path.join(os.path.dirname(__file__), "..", "dist")
if os.path.isdir(dist_path):
    index = os.path.join(dist_path, "index.html")
    check("dist/index.html exists", os.path.isfile(index))
else:
    print("  ⚠ dist/ not found — skip (dev mode, expected)")


# ══════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════

print(f"\n{'─' * 60}")
print(f"  Passed: {PASS}  |  Failed: {FAIL}")
print(f"{'─' * 60}")

if FAIL > 0:
    print("\n  FIX THE ABOVE BEFORE GOING LIVE.\n")
    sys.exit(1)
else:
    print("\n  All clear. Ready for demo.\n")
    sys.exit(0)
