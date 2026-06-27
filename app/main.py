"""Narrative Nexus — FastAPI application.

API routes prefixed with /api/. Vite dev server proxies /api/* to localhost:8000.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from db.sources import list_sources
from db.articles import list_articles
from db.clusters import list_clusters
from db.claims import list_claims
from db.snapshots import list_snapshots
from db.connection import get_db, init_db
from pipeline.scheduler import ScraperScheduler


@asynccontextmanager
async def lifespan(application: FastAPI):
    db_path = os.environ.get("NN_DB_PATH", "data/nn.db")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    init_db(db_path)
    application.state.db_path = db_path
    scheduler = ScraperScheduler(db_path=db_path)
    application.state.scraper = scheduler  # paused on startup
    yield
    scheduler.shutdown()


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
