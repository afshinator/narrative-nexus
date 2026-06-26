"""Narrative Nexus — FastAPI application.

API routes prefixed with /api/. Vite dev server proxies /api/* to localhost:8000.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.sources import list_sources
from db.articles import list_articles
from db.clusters import list_clusters
from db.claims import list_claims
from db.snapshots import list_snapshots
from db.connection import get_db

app = FastAPI(title="Narrative Nexus", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/sources")
def api_sources(active_only: bool = False):
    conn = get_db()
    try:
        sources = list_sources(conn, active_only=active_only)
        return {"sources": sources}
    finally:
        conn.close()


@app.get("/api/sources/{source_id}")
def api_source_by_id(source_id: int):
    conn = get_db()
    try:
        from db.sources import get_source
        source = get_source(conn, source_id)
        return {"source": source}
    finally:
        conn.close()


@app.get("/api/articles")
def api_articles(source_id: int | None = None, limit: int = 50, offset: int = 0):
    conn = get_db()
    try:
        articles = list_articles(conn, source_id=source_id, limit=limit, offset=offset)
        return {"articles": articles}
    finally:
        conn.close()


@app.get("/api/clusters")
def api_clusters(vertical: str | None = None, limit: int = 50, offset: int = 0):
    conn = get_db()
    try:
        clusters = list_clusters(conn, vertical=vertical, limit=limit, offset=offset)
        return {"clusters": clusters}
    finally:
        conn.close()


@app.get("/api/claims")
def api_claims(cluster_id: int | None = None, state: str | None = None, limit: int = 100, offset: int = 0):
    conn = get_db()
    try:
        claims = list_claims(conn, cluster_id=cluster_id, state=state, limit=limit, offset=offset)
        return {"claims": claims}
    finally:
        conn.close()


@app.get("/api/snapshots")
def api_snapshots(source_id: int | None = None, vertical: str | None = None, limit: int = 100, offset: int = 0):
    conn = get_db()
    try:
        snapshots = list_snapshots(conn, source_id=source_id, vertical=vertical, limit=limit, offset=offset)
        return {"snapshots": snapshots}
    finally:
        conn.close()
