"""Narrative Nexus — FastAPI application.

API routes prefixed with /api/. Vite dev server proxies /api/* to localhost:8000.
"""
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from db.sources import list_sources
from db.articles import list_articles
from db.clusters import list_clusters
from db.claims import list_claims
from db.snapshots import list_snapshots
from db.connection import get_db, init_db
from pipeline.scheduler import ScraperScheduler
from pipeline.runner_scheduler import start_pipeline_scheduler
from pipeline.provider_config import load_provider_config


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
    if not os.environ.get("NN_NO_PIPELINE"):
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

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/sources")
def api_sources(active_only: bool = False, conn = Depends(get_persistent_db)):
    sources = list_sources(conn, active_only=active_only)
    return {"sources": sources}


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
    claim_summary = {"total": 0, "absorbed": 0, "pending": 0}
    for r in claim_rows:
        claim_summary["total"] += r["cnt"]
        if r["state"] == "CONSENSUS_ABSORBED":
            claim_summary["absorbed"] = r["cnt"]
        elif r["state"] == "PENDING":
            claim_summary["pending"] = r["cnt"]

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
    return {"scores": scores}


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
    total_claims = sum(s["claims"] for s in sources)
    total_absorbed = sum(s["absorbed"] for s in sources)
    total_pending = sum(s["pending"] for s in sources)

    # Flat claim list with source domain
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

    claims = [dict(r) for r in claim_rows]

    return {
        "cluster": {"id": cluster["id"], "title": cluster["title"],
                     "vertical": cluster["vertical"]},
        "summary": {
            "totalClaims": total_claims,
            "absorbed": total_absorbed,
            "pending": total_pending,
            "sourceCount": len(sources),
        },
        "sources": sources,
        "claims": claims,
    }


# ── Scraper control endpoints ──────────────────────────────────────────

@app.get("/api/scraper/status")
def scraper_status(request: Request) -> dict:
    return request.app.state.scraper.status()


@app.post("/api/scraper/start")
def scraper_start(request: Request) -> dict:
    request.app.state.scraper.start()
    return {"status": "started"}


@app.post("/api/scraper/stop")
def scraper_stop(request: Request) -> dict:
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
