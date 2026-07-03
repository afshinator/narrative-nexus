#!/usr/bin/env python3
"""T4a helper: find story groups (shared keywords) across >= 3 sources in June 2026."""
import sqlite3, re, sys
from collections import defaultdict

conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT a.id, a.title, a.source_id, s.name as sn, a.published_at
    FROM articles a JOIN sources s ON s.id = a.source_id
    WHERE a.published_at >= '2026-06-01' AND a.published_at < '2026-07-01'
      AND a.body_status = 'AVAILABLE'
    ORDER BY a.published_at
""").fetchall()

STOP = set("that this with from have were their they will what when been more over into than some also other after about which would could said year says your them just like know make take time good back look well work only first much such part even".split())
P = re.compile(r'[,;:!?.\'\"()\[\]\-–—/]')

kw = defaultdict(list)
for r in rows:
    t = P.sub(" ", (r["title"] or "").lower())
    seen = set()
    for w in t.split():
        if len(w) >= 4 and w not in STOP and w not in seen:
            kw[w].append(r)
            seen.add(w)

# Sort by distinct source count descending
for w, arts in sorted(kw.items(), key=lambda x: (-len({a["sn"] for a in x[1]}), -len(x[1]))):
    srcs = {a["sn"] for a in arts}
    if len(srcs) >= 3 and len(arts) >= 3:
        print(f"KW='{w}'  srcs={len(srcs)}: {sorted(srcs)}  n={len(arts)}")
        for a in arts[:6]:
            print(f"  {a['id']:6d}  {a['sn']:20s}  {a['title'][:90]}")
        print()

conn.close()
