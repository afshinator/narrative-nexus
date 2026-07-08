"""Narrative Nexus — FastAPI application.

API routes prefixed with /api/. Vite dev server proxies /api/* to localhost:8000.
"""
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from db.sources import list_sources
from db.articles import list_articles
from db.clusters import list_clusters
from db.claims import list_claims
from db.snapshots import list_snapshots
from db.connection import get_db, init_db
from pipeline.scheduler import ScraperScheduler
from pipeline.runner_scheduler import start_pipeline_scheduler
from pipeline.provider_config import load_provider_config
from app.investigate_endpoint import investigate_stream_endpoint


# ── Provider config ──────────────────────────────────────────────────────

_PROVIDERS_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.json"
)


def _init_provider_state(app_state: Any) -> dict[str, Any]:
    """Load provider config into app state. Returns the config dict."""
    providers = load_provider_config(_PROVIDERS_CONFIG_PATH)
    # Runtime overrides: defaults from JSON, overridable via PUT endpoint
    app_state.providers = dict(providers["defaults"])
    app_state.provider_catalog = providers["providers"]
    return providers


@asynccontextmanager
async def lifespan(application: FastAPI):
    db_path = os.environ.get("NN_DB_PATH", "data/nn.db")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    init_db(db_path)
    application.state.db_path = db_path

    # Provider config — single source of truth
    _init_provider_state(application.state)

    # Scraper — paused on startup, controlled via /api/scraper/start|stop
    scraper_scheduler = ScraperScheduler(db_path=db_path)
    application.state.scraper = scraper_scheduler  # paused on startup

    # Pipeline runner — daily consensus + snapshot computation
    pipeline_scheduler = None
    if os.environ.get("NN_ENABLE_PIPELINE"):
        pipeline_scheduler = start_pipeline_scheduler(
            db_path,
            provider_overrides=application.state.providers,
        )
        application.state.pipeline = pipeline_scheduler

    yield

    scraper_scheduler.shutdown()
    if pipeline_scheduler is not None:
        pipeline_scheduler.shutdown(wait=False)


app = FastAPI(title="Narrative Nexus", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Database dependency ────────────────────────────────────────────────

def get_persistent_db(request: Request):
    """FastAPI dependency: yields a connection to the persistent database."""
    conn = get_db(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


# ── Routes ─────────────────────────────────────────────────────────────


def _get_latest_archetype(conn, source_id: int, vertical: str) -> str | None:
    """Return the stored archetype from the latest snapshot for source+vertical.

    The pipeline computes archetype from percentile-ranked R_orig/R_val vs
    panel median and stores it in the snapshots table.  This is the canonical
    value — the profile endpoint returns it directly instead of recomputing
    from a different median, which resolves the FV3 median-conflict where
    the scatter (stored, median 52/48) and profile (computed, median 76/0)
    produced different archetypes for the same source.
    """
    row = conn.execute(
        "SELECT archetype, r_orig, r_val FROM snapshots "
        "WHERE source_id = ? AND vertical = ? "
        "ORDER BY date DESC LIMIT 1",
        (source_id, vertical),
    ).fetchone()
    if not row:
        return None
    # Null contract: if r_orig or r_val is NULL, archetype is null
    # even if the DB stored a value.
    if row["r_orig"] is None or row["r_val"] is None:
        return None
    return row["archetype"]


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/sources")
def api_sources(active_only: bool = False, conn = Depends(get_persistent_db)):
    """Return all sources with archetype per vertical from latest snapshots.

    Archetype is read from the snapshots table (computed by the pipeline using
    panel medians of percentile-ranked R_orig/R_val across active sources).
    Sources with NULL R_orig or R_val get archetype=null per the null contract.
    """
    sources = list_sources(conn, active_only=active_only)

    # Latest date in snapshots — one query for all sources
    latest_date_row = conn.execute(
        "SELECT MAX(date) FROM snapshots"
    ).fetchone()
    latest_date = latest_date_row[0] if latest_date_row else None

    # Build archetype per (source_id, vertical) from latest snapshots
    archetype_map: dict[tuple[int, str], str | None] = {}
    if latest_date:
        rows = conn.execute(
            """SELECT source_id, vertical, r_orig, r_val, archetype
               FROM snapshots
               WHERE date = ?""",
            (latest_date,),
        ).fetchall()
        for r in rows:
            sid = r["source_id"]
            vert = r["vertical"]
            r_orig = r["r_orig"]
            r_val = r["r_val"]
            # Null contract: if either R_orig or R_val is NULL, archetype is null
            if r_orig is not None and r_val is not None:
                archetype_map[(sid, vert)] = r["archetype"]
            else:
                archetype_map[(sid, vert)] = None

    # Enrich each source with archetypes dict
    result = []
    for src in sources:
        sid = src["id"]
        src["archetypes"] = {
            vert: archetype_map.get((sid, vert))
            for vert in ["geopolitics", "economics", "technology"]
        }
        result.append(src)

    return {"sources": result}


@app.get("/api/sources/{source_id}")
def api_source_by_id(source_id: int, conn = Depends(get_persistent_db)):
    from db.sources import get_source
    source = get_source(conn, source_id)
    return {"source": source}


@app.get("/api/sources/{source_id}/profile")
def api_source_profile(
    source_id: int,
    vertical: str = "geopolitics",
    conn = Depends(get_persistent_db),
):
    """Return daily snapshots mapped to relative days, tier averages, and panel medians.

    Snapshots are ordered by date and assigned sequential day numbers starting from 0.
    tierAvg is 6 values (R_orig through R_correct) averaged across sources in the same tier.
    panelMedian is {orig, val} median across all active sources.
    """
    from db.sources import get_source
    from statistics import median

    source = get_source(conn, source_id)
    if source is None:
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Source not found"}, status_code=404)

    # ── Snapshots with day mapping ──────────────────────────────────────
    # ponytail: limit to last 180 days to avoid 166KB payloads (1200+ snapshots).
    # The frontend only shows the last 90 days (DAY_MAX).
    row_count = conn.execute(
        "SELECT COUNT(*) FROM snapshots WHERE source_id = ? AND vertical = ?",
        (source_id, vertical),
    ).fetchone()[0]
    skip = max(0, row_count - 180)
    rows = conn.execute(
        """SELECT date, r_orig, r_val, r_speed, r_frame, r_edit, r_correct
           FROM snapshots
           WHERE source_id = ? AND vertical = ?
           ORDER BY date
           LIMIT 180 OFFSET ?""",
        (source_id, vertical, skip),
    ).fetchall()

    snapshots = []
    for day, row in enumerate(rows):
        snapshots.append({
            "day": day,
            "date": row["date"],
            "sourceId": source_id,
            "vertical": vertical,
            "R_orig": row["r_orig"],
            "R_val": row["r_val"],
            "R_speed": row["r_speed"],
            "R_frame": row["r_frame"],
            "R_edit": row["r_edit"],
            "R_correct": row["r_correct"],
        })

    # ── Tier averages (6 dimensions) ────────────────────────────────────
    tier_rows = conn.execute(
        """SELECT AVG(sn.r_orig), AVG(sn.r_val), AVG(sn.r_speed),
                  AVG(sn.r_frame), AVG(sn.r_edit), AVG(sn.r_correct)
           FROM snapshots sn
           JOIN sources s ON s.id = sn.source_id
           WHERE s.tier = ? AND sn.vertical = ? AND sn.r_val IS NOT NULL""",
        (source["tier"], vertical),
    ).fetchone()

    tier_avg = [tier_rows[i] for i in range(6)]
    if all(v is None for v in tier_avg):
        tier_avg = None

    # ── Panel medians ───────────────────────────────────────────────────
    rows = conn.execute(
        "SELECT r_orig, r_val FROM snapshots WHERE vertical = ? "
        "AND r_orig IS NOT NULL AND r_val IS NOT NULL",
        (vertical,),
    ).fetchall()
    orig_vals = [r["r_orig"] for r in rows]
    val_vals = [r["r_val"] for r in rows]
    panel_median = {
        "orig": median(orig_vals) if orig_vals else None,
        "val": median(val_vals) if val_vals else None,
    }

    # ── Silent edits ────────────────────────────────────────────────────
    edit_rows = conn.execute(
        """SELECT se.id, se.change_ratio, se.stored_body_length,
                  se.fetched_body_length, se.detected_at,
                  a.url AS article_url, a.title AS article_title
           FROM silent_edits se
           JOIN articles a ON a.id = se.article_id
           WHERE a.source_id = ?
           ORDER BY se.detected_at DESC""",
        (source_id,),
    ).fetchall()
    edits = [dict(r) for r in edit_rows]

    # ── Claim summary ───────────────────────────────────────────────────
    claim_rows = conn.execute(
        """SELECT cl.state, COUNT(DISTINCT cl.id) AS cnt
           FROM claims cl
           JOIN claim_sources cs ON cs.claim_id = cl.id
           WHERE cs.source_id = ?
           GROUP BY cl.state""",
        (source_id,),
    ).fetchall()
    claim_summary = {"total": 0, "absorbed": 0, "pending": 0, "unresolved": 0}
    for r in claim_rows:
        claim_summary["total"] += r["cnt"]
        if r["state"] == "CONSENSUS_ABSORBED":
            claim_summary["absorbed"] = r["cnt"]
        elif r["state"] == "PENDING":
            claim_summary["pending"] = r["cnt"]
        elif r["state"] == "UNRESOLVED":
            claim_summary["unresolved"] = r["cnt"]

    # ── Events (aggregated) ─────────────────────────────────────────────
    # ponytail: all edits/absorptions on 2026-06-30, after snapshots end at 2026-06-28
    # Map to day 90 (the DayScrubber max)
    events = []
    event_day = 90
    if claim_summary["absorbed"] > 0:
        events.append({
            "day": event_day,
            "type": "CLAIM_ABSORBED",
            "title": f"{claim_summary['absorbed']} claims absorbed",
            "detail": "",
        })
    if len(edits) > 0:
        events.append({
            "day": event_day,
            "type": "SILENT_EDIT",
            "title": f"{len(edits)} edits detected",
            "detail": "",
        })

    return {
        "snapshots": snapshots,
        "tierAvg": tier_avg,
        "panelMedian": panel_median,
        "archetype": _get_latest_archetype(conn, source_id, vertical),
        "events": events,
        "edits": edits,
        "claimSummary": claim_summary,
    }


@app.get("/api/scores")
def api_scores(vertical: str = "geopolitics", conn = Depends(get_persistent_db)):
    """Return latest ReputationScore per source for the given vertical."""
    rows = conn.execute(
        """SELECT s.domain, sn.vertical, sn.r_orig, sn.r_val, sn.r_speed,
                  sn.r_frame, sn.r_edit, sn.r_correct
           FROM sources s
           JOIN snapshots sn ON sn.source_id = s.id
           WHERE sn.vertical = ?
             AND sn.date = (SELECT MAX(date) FROM snapshots
                            WHERE source_id = s.id AND vertical = ?)""",
        (vertical, vertical),
    ).fetchall()
    drange = conn.execute(
        "SELECT MIN(date), MAX(date) FROM snapshots WHERE vertical=?",
        (vertical,),
    ).fetchone()
    scores = [
        {
            "sourceId": r["domain"],
            "vertical": r["vertical"],
            "R_orig": r["r_orig"],
            "R_val": r["r_val"],
            "R_speed": r["r_speed"],
            "R_frame": r["r_frame"],
            "R_edit": r["r_edit"],
            "R_correct": r["r_correct"],
        }
        for r in rows
    ]
    return {
        "scores": scores,
        "date_min": drange[0] if drange else None,
        "date_max": drange[1] if drange else None,
    }


@app.get("/api/articles")
def api_articles(source_id: int | None = None, limit: int = 50, offset: int = 0, conn = Depends(get_persistent_db)):
    articles = list_articles(conn, source_id=source_id, limit=limit, offset=offset)
    return {"articles": articles}


@app.get("/api/clusters")
def api_clusters(vertical: str | None = None, limit: int = 50, offset: int = 0, conn = Depends(get_persistent_db)):
    clusters = list_clusters(conn, vertical=vertical, limit=limit, offset=offset)
    return {"clusters": clusters}


@app.get("/api/claims")
def api_claims(cluster_id: int | None = None, state: str | None = None, limit: int = 100, offset: int = 0, conn = Depends(get_persistent_db)):
    claims = list_claims(conn, cluster_id=cluster_id, state=state, limit=limit, offset=offset)
    return {"claims": claims}


@app.get("/api/snapshots")
def api_snapshots(source_id: int | None = None, vertical: str | None = None, limit: int = 100, offset: int = 0, conn = Depends(get_persistent_db)):
    snapshots = list_snapshots(conn, source_id=source_id, vertical=vertical, limit=limit, offset=offset)
    return {"snapshots": snapshots}


@app.get("/api/timeline/{cluster_id}")
def api_timeline(cluster_id: int, conn = Depends(get_persistent_db)):
    """Return claims in a cluster grouped by source, sorted by first_seen_at."""
    from db.clusters import get_cluster

    cluster = get_cluster(conn, cluster_id)
    if cluster is None:
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Cluster not found"}, status_code=404)

    rows = conn.execute(
        """SELECT cs.first_seen_at, s.domain, s.tier,
                  cl.id, cl.text, cl.state, cl.absorbed_at, cl.created_at
           FROM claims cl
           JOIN claim_sources cs ON cs.claim_id = cl.id
           JOIN sources s ON s.id = cs.source_id
           WHERE cl.cluster_id = ?
           ORDER BY cs.first_seen_at""",
        (cluster_id,),
    ).fetchall()

    # ponytail: group by source domain, preserving first_seen order
    sources: dict[str, dict] = {}
    for r in rows:
        domain = r["domain"]
        if domain not in sources:
            sources[domain] = {"domain": domain, "tier": r["tier"], "claims": []}
        sources[domain]["claims"].append({
            "id": r["id"],
            "text": r["text"],
            "state": r["state"],
            "absorbed_at": r["absorbed_at"],
            "first_seen_at": r["first_seen_at"],
            "created_at": r["created_at"],
        })

    return {
        "cluster": {"id": cluster["id"], "title": cluster["title"]},
        "sources": list(sources.values()),
    }


@app.get("/api/clusters/{cluster_id}/report")
def api_cluster_report(cluster_id: int, conn = Depends(get_persistent_db)):
    """Return aggregate stats + claims with source domain for one cluster."""
    from db.clusters import get_cluster

    cluster = get_cluster(conn, cluster_id)
    if cluster is None:
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Cluster not found"}, status_code=404)

    # Source breakdown
    src_rows = conn.execute(
        """SELECT s.domain, s.tier, COUNT(DISTINCT cl.id) AS claims,
                  SUM(CASE WHEN cl.state = 'CONSENSUS_ABSORBED' THEN 1 ELSE 0 END) AS absorbed,
                  SUM(CASE WHEN cl.state = 'PENDING' THEN 1 ELSE 0 END) AS pending
           FROM claims cl
           JOIN claim_sources cs ON cs.claim_id = cl.id
           JOIN sources s ON s.id = cs.source_id
           WHERE cl.cluster_id = ?
           GROUP BY s.id
           ORDER BY MIN(cs.first_seen_at)""",
        (cluster_id,),
    ).fetchall()

    sources = [dict(r) for r in src_rows]
    # D4.1: count distinct claims directly (not sum of per-source counts —
    # a claim with multiple claim_sources would be double-counted).
    total_claims = conn.execute(
        "SELECT COUNT(*) FROM claims WHERE cluster_id = ?",
        (cluster_id,),
    ).fetchone()[0]
    # Count DISTINCT absorbed claims (avoid per-source double-count from
    # claim_sources JOIN — a merged claim appears under multiple sources).
    total_absorbed = conn.execute(
        "SELECT COUNT(DISTINCT id) FROM claims "
        "WHERE cluster_id = ? AND state = 'CONSENSUS_ABSORBED'",
        (cluster_id,),
    ).fetchone()[0]
    total_pending = conn.execute(
        "SELECT COUNT(DISTINCT id) FROM claims "
        "WHERE cluster_id = ? AND state = 'PENDING'",
        (cluster_id,),
    ).fetchone()[0]

    # Flat claim list with source domains (deduplicated — one row per claim,
    # with aggregated domains for claims that have multiple claim_sources).
    claim_rows = conn.execute(
        """SELECT cl.id, cl.text, cl.state, cl.absorbed_at, cl.created_at,
                  s.domain
           FROM claims cl
           JOIN claim_sources cs ON cs.claim_id = cl.id
           JOIN sources s ON s.id = cs.source_id
           WHERE cl.cluster_id = ?
           ORDER BY cl.created_at DESC""",
        (cluster_id,),
    ).fetchall()

    claims_by_id: dict[int, dict] = {}
    for r in claim_rows:
        cid = r["id"]
        if cid not in claims_by_id:
            claims_by_id[cid] = {
                "id": r["id"],
                "text": r["text"],
                "state": r["state"],
                "absorbed_at": r["absorbed_at"],
                "created_at": r["created_at"],
                "domains": [],
            }
        claims_by_id[cid]["domains"].append(r["domain"])
    claims = list(claims_by_id.values())

    # K5a: dynamic absorption strip — per-cluster, not hardcoded
    # Top sources (by absorbed count, then total count)
    top_srcs = sorted(
        [s for s in sources if s["absorbed"] > 0],
        key=lambda s: (s["absorbed"], s["claims"]), reverse=True,
    )[:2]
    top_src_names = [s["domain"] for s in top_srcs]

    # Pool: Tier 1-2 sources in this cluster
    pool_srcs = [s for s in sources if s["tier"] in (1, 2)]
    pool_total = len(pool_srcs)
    pool_absorbed = len([s for s in pool_srcs if s["absorbed"] > 0])
    pool_pct = round(100 * pool_absorbed / pool_total) if pool_total > 0 else 0
    abstaining = [s["domain"] for s in pool_srcs if s["absorbed"] == 0]

    # M2: distinct first_seen_at days for timeline health check
    distinct_days = conn.execute(
        "SELECT COUNT(DISTINCT DATE(cs.first_seen_at)) FROM claim_sources cs "
        "JOIN claims c ON c.id = cs.claim_id "
        "WHERE c.cluster_id = ? AND cs.first_seen_at != '' AND cs.first_seen_at IS NOT NULL",
        (cluster_id,),
    ).fetchone()[0]
    # UX27: suppress timeline link when data is incomplete (62% empty for 924)
    empty_dates = conn.execute(
        "SELECT COUNT(*) FROM claim_sources cs "
        "JOIN claims c ON c.id = cs.claim_id "
        "WHERE c.cluster_id = ? AND (cs.first_seen_at = '' OR cs.first_seen_at IS NULL)",
        (cluster_id,),
    ).fetchone()[0]

    # UX32: coverage stats — article count, date window
    article_count = conn.execute(
        "SELECT COUNT(DISTINCT article_id) FROM claims WHERE cluster_id = ?",
        (cluster_id,),
    ).fetchone()[0]
    date_window = conn.execute(
        "SELECT MIN(a.published_at), MAX(a.published_at) "
        "FROM articles a INNER JOIN claims c ON c.article_id = a.id "
        "WHERE c.cluster_id = ? AND a.published_at IS NOT NULL",
        (cluster_id,),
    ).fetchone()

    return {
        "cluster": {"id": cluster["id"], "title": cluster["title"],
                     "vertical": cluster["vertical"]},
        "summary": {
            "totalClaims": total_claims,
            "absorbed": total_absorbed,
            "pending": total_pending,
            "sourceCount": len(sources),
            "articleCount": article_count,
            "coverageStart": date_window[0] if date_window else None,
            "coverageEnd": date_window[1] if date_window else None,
            "topSourceNames": top_src_names,
            "poolSize": pool_total,
            "poolParticipating": pool_absorbed,
            "poolPct": pool_pct,
            "abstainingNames": abstaining,
            "distinctDays": distinct_days,
            "emptyDateCount": empty_dates,
        },
        "sources": sources,
        "claims": claims,
    }


# ── Coverage Landscape endpoint (Track A — T1) ─────────────────────────

@app.get("/api/coverage-landscape")
def api_coverage_landscape(conn=Depends(get_persistent_db)):
    """Per-source coverage stats: total claims, solo claims, solo share.

    Returns one row per source with solo_claims = claims in clusters where
    that source is the only distinct source. No vertical filter — pan-vertical.
    """
    rows = conn.execute("""
        SELECT s.id as source_id, s.name, s.tier,
               COUNT(cl.id) as total_claims,
               SUM(CASE WHEN cluster_srcs.src_count = 1 THEN 1 ELSE 0 END) as solo_claims,
               ROUND(CASE WHEN COUNT(cl.id) > 0
                     THEN 100.0 * SUM(CASE WHEN cluster_srcs.src_count = 1 THEN 1 ELSE 0 END) / COUNT(cl.id)
                     ELSE 0 END, 1) as solo_share_pct,
               CASE WHEN SUM(CASE WHEN cl.state = 'CONSENSUS_ABSORBED' THEN 1 ELSE 0 END) > 0
                    THEN 1 ELSE 0 END as has_absorbed_claims
        FROM sources s
        LEFT JOIN articles a ON a.source_id = s.id
        LEFT JOIN claims cl ON cl.article_id = a.id
        LEFT JOIN (
            SELECT c2.cluster_id,
                   COUNT(DISTINCT a3.source_id) as src_count
            FROM claims c2
            JOIN articles a3 ON a3.id = c2.article_id
            GROUP BY c2.cluster_id
        ) cluster_srcs ON cluster_srcs.cluster_id = cl.cluster_id
        GROUP BY s.id
        ORDER BY solo_share_pct DESC, total_claims DESC
    """).fetchall()

    return {
        "sources": [dict(r) for r in rows],
        "totalSources": len(rows),
    }


# ── Scraper control endpoints ──────────────────────────────────────────

@app.get("/api/scraper/status")
def scraper_status(request: Request) -> dict:
    data = request.app.state.scraper.status()
    data["readonly"] = _is_readonly()
    return data


def _is_readonly() -> bool:
    """Checks env or sentinel file — env vars lost by uvicorn worker spawns."""
    return bool(
        os.environ.get("NN_READONLY")
        or os.path.exists(os.path.join(os.path.dirname(__file__), "..", ".readonly"))
    )


@app.post("/api/scraper/start")
def scraper_start(request: Request) -> dict:
    if _is_readonly():
        raise HTTPException(status_code=403, detail="read-only demo")
    request.app.state.scraper.start()
    return {"status": "started"}


@app.post("/api/scraper/stop")
def scraper_stop(request: Request) -> dict:
    if _is_readonly():
        raise HTTPException(status_code=403, detail="read-only demo")
    request.app.state.scraper.stop()
    return {"status": "stopped"}


# ── Provider config endpoints ────────────────────────────────────────────

@app.get("/api/config/providers")
def get_provider_config(request: Request) -> dict:
    """Return current provider assignments (defaults + runtime overrides)."""
    return {
        "providers": request.app.state.providers,
    }


@app.put("/api/config/providers")
def update_provider_config(request: Request, body: dict[str, str]) -> dict:
    """Update one or more provider assignments at runtime.

    Body: {"agent2_llm": "fireworks", "agent1_embedding": "local-cpu"}
    Only keys matching known agent slots are accepted.
    """
    valid_slots = {
        "agent1_embedding", "agent1_llm",
        "agent2_llm", "agent4_llm",
    }
    updated = 0
    for key, value in body.items():
        if key in valid_slots and isinstance(value, str):
            request.app.state.providers[key] = value
            updated += 1
    return {"updated": updated, "providers": request.app.state.providers}


@app.get("/api/config/providers/available")
def get_available_providers(request: Request) -> dict:
    """Return the full provider catalog from config/providers.json.

    Used by the Pipeline Flow frontend to populate dropdown options.
    """
    return {"providers": request.app.state.provider_catalog}


# ── Investigate SSE endpoint (Track B Phase 2) ──────────────────────────
app.post("/api/investigate/stream")(investigate_stream_endpoint)


# ── SPA Frontend Serving (D4.0) ─────────────────────────────────────────
# Serves the Vite-built dist/ directory. All routes not matched by /api/*
# fall back to index.html for client-side routing (/source/5, /cluster/966,
# etc. work as deep links). Static files under dist/ are served directly.

import os as _os

_DIST_DIR = _os.path.join(_os.path.dirname(__file__), "..", "dist")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str = ""):
    """Serve SPA frontend — API routes take priority, everything else is SPA.

    /                → dist/index.html
    /assets/app.js   → dist/assets/app.js (if exists)
    /source/5        → dist/index.html (SPA fallback)
    /cluster/966     → dist/index.html (SPA fallback)
    """
    # Direct file match: serve static assets under dist/
    if full_path:
        file_path = _os.path.join(_DIST_DIR, full_path)
        if _os.path.isfile(file_path):
            return FileResponse(file_path)
    # SPA fallback: all client-side routes serve index.html
    return FileResponse(_os.path.join(_DIST_DIR, "index.html"))
