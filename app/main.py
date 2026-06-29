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
    rows = conn.execute(
        """SELECT date, r_orig, r_val, r_speed, r_frame, r_edit, r_correct
           FROM snapshots
           WHERE source_id = ? AND vertical = ?
           ORDER BY date""",
        (source_id, vertical),
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

    return {
        "snapshots": snapshots,
        "tierAvg": tier_avg,
        "panelMedian": panel_median,
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
