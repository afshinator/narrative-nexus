"""Daily snapshot writer — batch computes reputation scores and writes one row per source×vertical."""
import sqlite3
from datetime import datetime, timezone

from db.sources import list_sources
from db.snapshots import insert_snapshot
from pipeline.archetype import get_archetype
from pipeline.reputation import (
    compute_r_orig,
    compute_r_val,
    compute_r_speed,
    compute_r_frame,
    compute_r_edit,
    compute_r_correct,
)

VERTICALS = ["geopolitics", "economics", "technology"]


def write_daily_snapshots(conn: sqlite3.Connection, date_str: str | None = None) -> int:
    """Write one snapshot row per active source × vertical for the given date."""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    sources = list_sources(conn, active_only=True)
    count = 0

    for source in sources:
        sid = source["id"]
        median_orig, median_val = _panel_medians(conn)

        for vertical in VERTICALS:
            originated, total, absorbed, delays = _query_claim_stats(conn, sid, vertical)
            r_orig = compute_r_orig(originated, total)
            r_val = compute_r_val(absorbed, originated)
            r_speed = compute_r_speed(delays)
            archetype = get_archetype(r_orig, r_val, median_orig, median_val)

            try:
                insert_snapshot(
                    conn,
                    source_id=sid,
                    vertical=vertical,
                    date=date_str,
                    r_orig=r_orig,
                    r_val=r_val,
                    r_speed=r_speed,
                    r_frame=None,
                    r_edit=None,
                    r_correct=None,
                    archetype=archetype,
                )
                count += 1
            except sqlite3.IntegrityError:
                pass

    return count


def _query_claim_stats(conn: sqlite3.Connection, source_id: int, vertical: str) -> tuple[int, int, int, list[float]]:
    """Return (originated, total, absorbed, delays) for a source in a given vertical."""
    rows = conn.execute(
        """SELECT COUNT(*) FROM claim_sources cs
           JOIN claims c ON c.id = cs.claim_id
           JOIN clusters cl ON cl.id = c.cluster_id
           WHERE cs.source_id = ? AND cl.vertical = ?
           AND cs.first_seen_at = (
               SELECT MIN(cs2.first_seen_at) FROM claim_sources cs2 WHERE cs2.claim_id = cs.claim_id
           )""",
        (source_id, vertical),
    ).fetchone()
    originated = rows[0] if rows else 0

    rows = conn.execute("SELECT COUNT(*) FROM claims c JOIN clusters cl ON cl.id = c.cluster_id WHERE cl.vertical = ?", (vertical,)).fetchone()
    total = rows[0] if rows else 0

    rows = conn.execute(
        """SELECT COUNT(*) FROM claim_sources cs
           JOIN claims c ON c.id = cs.claim_id
           JOIN clusters cl ON cl.id = c.cluster_id
           WHERE cs.source_id = ? AND cl.vertical = ?
           AND c.state = 'CONSENSUS_ABSORBED'
           AND cs.first_seen_at = (
               SELECT MIN(cs2.first_seen_at) FROM claim_sources cs2 WHERE cs2.claim_id = cs.claim_id
           )""",
        (source_id, vertical),
    ).fetchone()
    absorbed = rows[0] if rows else 0

    delay_rows = conn.execute(
        """SELECT julianday(c.absorbed_at) - julianday(cs.first_seen_at) AS delay
           FROM claim_sources cs
           JOIN claims c ON c.id = cs.claim_id
           JOIN clusters cl ON cl.id = c.cluster_id
           WHERE cs.source_id = ? AND cl.vertical = ?
           AND c.state = 'CONSENSUS_ABSORBED'
           AND c.absorbed_at IS NOT NULL
           AND cs.first_seen_at = (
               SELECT MIN(cs2.first_seen_at) FROM claim_sources cs2 WHERE cs2.claim_id = cs.claim_id
           )""",
        (source_id, vertical),
    ).fetchall()
    delays = [row[0] for row in delay_rows if row[0] is not None]

    return originated, total, absorbed, delays


# ponytail: panel medians computed from current snapshots, fallback 50
def _panel_medians(conn: sqlite3.Connection) -> tuple[float, float]:
    rows = conn.execute(
        "SELECT r_orig, r_val FROM snapshots WHERE r_orig IS NOT NULL AND r_val IS NOT NULL"
    ).fetchall()
    if len(rows) < 2:
        return 50.0, 50.0
    origs = sorted(r[0] for r in rows)
    vals = sorted(r[1] for r in rows)
    mid = len(origs) // 2
    median_orig = origs[mid] if len(origs) % 2 else (origs[mid - 1] + origs[mid]) / 2
    median_val = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2
    return median_orig, median_val
