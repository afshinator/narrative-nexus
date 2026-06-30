"""Daily reputation snapshot computation — pure functions.

Computes R_orig, R_val, R_speed per source per vertical from claim data.
R_frame, R_edit, R_correct are NULL until their respective agents are built
(design doc §3 Data Format Contracts).
"""
import sqlite3
from statistics import median

from db.sources import list_sources
from db.snapshots import insert_snapshot
from pipeline.archetype import get_archetype


def compute_r_orig_raw(conn: sqlite3.Connection, *, as_of: str | None = None) -> dict[int, int]:
    """Count claims where each source was the first reporter.

    If as_of is provided (ISO datetime string), only claims with
    created_at <= as_of are counted.  Used by the seed script to
    generate date-filtered reputation snapshots.

    Returns {source_id: origination_count}.
    """
    params: list = []
    date_filter = ""
    if as_of is not None:
        date_filter = "WHERE c.created_at <= ?"
        params.append(as_of)

    rows = conn.execute(f"""
        SELECT cs.source_id, COUNT(*) as cnt
        FROM claim_sources cs
        INNER JOIN (
            SELECT claim_id, MIN(first_seen_at) as first_seen
            FROM claim_sources
            GROUP BY claim_id
        ) firsts ON cs.claim_id = firsts.claim_id
            AND cs.first_seen_at = firsts.first_seen
        INNER JOIN claims c ON cs.claim_id = c.id
        INNER JOIN clusters cl ON c.cluster_id = cl.id
        {date_filter}
        GROUP BY cs.source_id
    """, params).fetchall()

    return {row["source_id"]: row["cnt"] for row in rows}


def compute_r_val_raw(conn: sqlite3.Connection, *, as_of: str | None = None) -> dict[int, float | None]:
    """Ratio of absorbed to originated claims per source.

    If as_of is provided, only claims with created_at <= as_of are counted.

    Returns {source_id: ratio} where ratio = absorbed_count / originated_count.
    None when a source originated zero claims.
    """
    originated = compute_r_orig_raw(conn, as_of=as_of)

    params: list = []
    date_filter = ""
    if as_of is not None:
        date_filter = "AND c.created_at <= ?"
        params.append(as_of)

    rows = conn.execute(f"""
        SELECT cs.source_id, COUNT(*) as cnt
        FROM claim_sources cs
        INNER JOIN (
            SELECT claim_id, MIN(first_seen_at) as first_seen
            FROM claim_sources
            GROUP BY claim_id
        ) firsts ON cs.claim_id = firsts.claim_id
            AND cs.first_seen_at = firsts.first_seen
        INNER JOIN claims c ON cs.claim_id = c.id
        WHERE c.state = 'CONSENSUS_ABSORBED'
          {date_filter}
        GROUP BY cs.source_id
    """, params).fetchall()

    absorbed = {row["source_id"]: row["cnt"] for row in rows}

    result: dict[int, float | None] = {}
    for sid, orig in originated.items():
        abs_count = absorbed.get(sid, 0)
        result[sid] = abs_count / orig if orig > 0 else None
    return result


def compute_r_speed_raw(conn: sqlite3.Connection, *, as_of: str | None = None) -> dict[int, float | None]:
    """Median days between origination and absorption for absorbed claims.

    If as_of is provided, only claims with created_at <= as_of are counted.

    Returns {source_id: median_days}. None when a source has no absorbed claims.
    """
    params: list = []
    date_filter = ""
    if as_of is not None:
        date_filter = "AND c.created_at <= ?"
        params.append(as_of)

    rows = conn.execute(f"""
        SELECT cs.source_id,
               (julianday(c.absorbed_at) - julianday(c.created_at)) as days
        FROM claim_sources cs
        INNER JOIN (
            SELECT claim_id, MIN(first_seen_at) as first_seen
            FROM claim_sources
            GROUP BY claim_id
        ) firsts ON cs.claim_id = firsts.claim_id
            AND cs.first_seen_at = firsts.first_seen
        INNER JOIN claims c ON cs.claim_id = c.id
        WHERE c.state = 'CONSENSUS_ABSORBED'
          AND c.absorbed_at IS NOT NULL
          AND c.created_at IS NOT NULL
          {date_filter}
    """, params).fetchall()

    by_source: dict[int, list[float]] = {}
    for row in rows:
        sid = row["source_id"]
        days = row["days"]
        if days is not None and days >= 0:
            by_source.setdefault(sid, []).append(days)

    result: dict[int, float | None] = {}
    all_sources = {s["id"] for s in list_sources(conn)}
    for sid in all_sources:
        values = by_source.get(sid, [])
        result[sid] = median(values) if values else None
    return result


def percentile_rank(raw: dict[int, float]) -> dict[int, float]:
    """Convert raw values to 0–100 percentile ranks.

    Uses the standard percentile formula: (rank - 1) / (N - 1) * 100.
    Tied values get the same rank (minimum rank for the group).
    """
    if not raw:
        return {}

    sorted_items = sorted(raw.items(), key=lambda x: x[1])
    n = len(sorted_items)

    result: dict[int, float] = {}
    i = 0
    while i < n:
        j = i
        while j < n and sorted_items[j][1] == sorted_items[i][1]:
            j += 1
        pct = (i / (n - 1)) * 100 if n > 1 else 100.0
        for k in range(i, j):
            result[sorted_items[k][0]] = pct
        i = j

    return result


def compute_r_edit_raw(conn: sqlite3.Connection, *, as_of: str | None = None) -> dict[int, float | None]:
    """Silent edit rate per source — edits / articles ratio.

    If as_of is provided, only silent_edits with detected_at <= as_of
    are counted.  Used by the seed script for date-filtered snapshots.

    Returns {source_id: ratio} where ratio = edit_count / article_count.
    None when a source has zero articles.
    """
    # Article count per source (all time — no date filter)
    art_rows = conn.execute(
        "SELECT source_id, COUNT(*) as cnt FROM articles GROUP BY source_id"
    ).fetchall()
    article_counts = {row["source_id"]: row["cnt"] for row in art_rows}

    # Edit count per source, with optional as_of filter
    params: list = []
    date_filter = ""
    if as_of is not None:
        date_filter = "AND se.detected_at <= ?"
        params.append(as_of)

    edit_rows = conn.execute(f"""
        SELECT a.source_id, COUNT(se.id) as cnt
        FROM silent_edits se
        JOIN articles a ON a.id = se.article_id
        WHERE 1=1 {date_filter}
        GROUP BY a.source_id
    """, params).fetchall()
    edit_counts = {row["source_id"]: row["cnt"] for row in edit_rows}

    result: dict[int, float | None] = {}
    all_sources = {s["id"] for s in list_sources(conn)}
    for sid in all_sources:
        art_cnt = article_counts.get(sid, 0)
        if art_cnt == 0:
            result[sid] = None
        else:
            edit_cnt = edit_counts.get(sid, 0)
            result[sid] = edit_cnt / art_cnt
    return result


def compute_panel_medians(
    r_orig: dict[int, float],
    r_val: dict[int, float],
    active_ids: set[int],
) -> tuple[float, float]:
    """Compute panel median R_orig and R_val from active sources."""
    orig_vals = sorted(v for k, v in r_orig.items() if k in active_ids and v is not None)
    val_vals = sorted(v for k, v in r_val.items() if k in active_ids and v is not None)

    median_orig = median(orig_vals) if orig_vals else 50.0
    median_val = median(val_vals) if val_vals else 50.0
    return median_orig, median_val


def write_daily_snapshots(
    conn: sqlite3.Connection,
    date_str: str,
    vertical: str,
    r_orig: dict[int, float],
    r_val: dict[int, float],
    r_speed: dict[int, float],
    archetypes: dict[int, str],
    r_frame: dict[int, float | None] | None = None,
    r_edit: dict[int, float | None] | None = None,
    r_correct: dict[int, float | None] | None = None,
) -> int:
    """Write one snapshot row per source for the given date and vertical.

    Returns the number of rows inserted.
    """
    if r_frame is None:
        r_frame = {}
    if r_edit is None:
        r_edit = {}
    if r_correct is None:
        r_correct = {}

    sources = list_sources(conn)
    count = 0
    for src in sources:
        sid = src["id"]
        insert_snapshot(
            conn,
            source_id=sid,
            vertical=vertical,
            date=date_str,
            r_orig=r_orig.get(sid),
            r_val=r_val.get(sid),
            r_speed=r_speed.get(sid),
            r_frame=r_frame.get(sid),
            r_edit=r_edit.get(sid),
            r_correct=r_correct.get(sid),
            archetype=archetypes.get(sid),
        )
        count += 1
    return count
