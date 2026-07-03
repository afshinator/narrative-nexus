#!/usr/bin/env python3
"""T4a: Identify 15 real story groups across >=3 sources in June 2026."""
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

# Known distinct story groups based on title keyword analysis
# We identify groups where >=3 different sources cover the SAME event
# using distinctive multi-word phrases

GROUPS = {}

# 1. US-Iran Deal/War
GROUPS["US-Iran peace deal"] = [r for r in rows if "iran" in (r["title"] or "").lower() and ("deal" in (r["title"] or "").lower() or "talks" in (r["title"] or "").lower() or "sign" in (r["title"] or "").lower() or "memorandum" in (r["title"] or "").lower())]
# Dedupe by source, keep earliest
seen = {}
deduped = []
for r in GROUPS["US-Iran peace deal"]:
    if r["sn"] not in seen or r["published_at"] < seen[r["sn"]]["published_at"]:
        seen[r["sn"]] = r
GROUPS["US-Iran peace deal"] = sorted(seen.values(), key=lambda r: r["published_at"])

# 2. Venezuela Earthquakes
GROUPS["Venezuela earthquakes"] = [r for r in rows if ("venezuela" in (r["title"] or "").lower() and ("earthquake" in (r["title"] or "").lower() or "quake" in (r["title"] or "").lower())) or ("earthquake" in (r["title"] or "").lower() and "venezuela" in (r["title"] or "").lower())]

# 3. World Cup 2026
GROUPS["World Cup 2026"] = [r for r in rows if "world cup" in (r["title"] or "").lower() and "2026" in (r["title"] or "").lower()]

# 4. Supreme Court rulings (recent)
GROUPS["Supreme Court rulings"] = [r for r in rows if "supreme court" in (r["title"] or "").lower()]

# 5. South Korea drone warriors / military
GROUPS["South Korea drone military"] = [r for r in rows if "south korea" in (r["title"] or "").lower() and ("drone" in (r["title"] or "").lower() or "military" in (r["title"] or "").lower())]

# 6. Ukraine-Russia prisoner swap
GROUPS["Ukraine-Russia prisoner swap"] = [r for r in rows if ("ukraine" in (r["title"] or "").lower() or "russia" in (r["title"] or "").lower()) and ("prisoner" in (r["title"] or "").lower() or "swap" in (r["title"] or "").lower() or "pow" in (r["title"] or "").lower())]

# 7. Messi World Cup
GROUPS["Messi World Cup 2026"] = [r for r in rows if "messi" in (r["title"] or "").lower()]

# 8. Japan earthquake
GROUPS["Japan earthquake June 2026"] = [r for r in rows if "japan" in (r["title"] or "").lower() and ("earthquake" in (r["title"] or "").lower() or "quake" in (r["title"] or "").lower())]

# 9. Trump policy/actions
GROUPS["Trump policy June 2026"] = [r for r in rows if "trump" in (r["title"] or "").lower() and ("sign" in (r["title"] or "").lower() or "executive" in (r["title"] or "").lower() or "order" in (r["title"] or "").lower() or "ban" in (r["title"] or "").lower() or "policy" in (r["title"] or "").lower())]

# 10. Milei Argentina politics
GROUPS["Milei Argentina politics"] = [r for r in rows if "milei" in (r["title"] or "").lower() or "argentina" in (r["title"] or "").lower() and ("president" in (r["title"] or "").lower() or "government" in (r["title"] or "").lower())]

# 11. Pakistan period tax / sanitary products
GROUPS["Pakistan period tax"] = [r for r in rows if "pakistan" in (r["title"] or "").lower() and ("tax" in (r["title"] or "").lower() or "sanitary" in (r["title"] or "").lower() or "period" in (r["title"] or "").lower())]

# 12. China WTO / EU trade
GROUPS["China WTO EU trade"] = [r for r in rows if ("china" in (r["title"] or "").lower() or "chinese" in (r["title"] or "").lower()) and ("wto" in (r["title"] or "").lower() or "trade" in (r["title"] or "").lower() or "eu" in (r["title"] or "").lower())]

# 13. Taliban smartphone ban
GROUPS["Taliban smartphone ban"] = [r for r in rows if "taliban" in (r["title"] or "").lower() and ("phone" in (r["title"] or "").lower() or "smartphone" in (r["title"] or "").lower() or "device" in (r["title"] or "").lower())]

# 14. Fentanyl / opioid crisis
GROUPS["Fentanyl opioid crisis"] = [r for r in rows if "fentanyl" in (r["title"] or "").lower() or "opioid" in (r["title"] or "").lower()]

# 15. US SNAP benefits cuts
GROUPS["SNAP benefits cuts"] = [r for r in rows if "snap" in (r["title"] or "").lower() or "food stamp" in (r["title"] or "").lower() or "food benefit" in (r["title"] or "").lower()]

# Print each group: articles with IDs, titles, sources
for i, (name, arts) in enumerate(GROUPS.items(), 1):
    srcs = {a["sn"] for a in arts}
    if len(srcs) < 3:
        continue
    print(f"\n{'='*70}")
    print(f"GROUP {i}: {name}")
    print(f"  Sources: {len(srcs)} — {sorted(srcs)}")
    print(f"  Articles: {len(arts)}")
    for a in arts[:8]:
        print(f"    ID={a['id']:6d}  | {a['sn']:20s}  | {a['title'][:100]}")
    if len(arts) > 8:
        print(f"    ... and {len(arts)-8} more")

conn.close()
