#!/usr/bin/env python3
"""T4a final: Build 15 story group lists with article IDs, titles, sources."""
import sqlite3
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

def find(keywords, title_must_contain=None):
    """Find articles where title contains at least one keyword AND optionally a required phrase."""
    results = []
    for r in rows:
        t = (r["title"] or "").lower()
        if not any(kw in t for kw in keywords):
            continue
        if title_must_contain and title_must_contain not in t:
            continue
        results.append(r)
    return results

def group_report(name, articles):
    srcs = {a["sn"] for a in articles}
    print(f"\n--- {name} ---")
    print(f"  Sources: {len(srcs)} — {sorted(srcs)}")
    print(f"  Articles: {len(articles)}")
    for a in articles[:6]:
        print(f"    ID={a['id']} | {a['sn']} | {a['title'][:90]}")
    return articles

# 15 curated groups — clearly the same real-world event
groups = {}

# 1. US-Iran peace deal (15 sources)
groups["US-Iran peace deal"] = find(["iran"], None)
groups["US-Iran peace deal"] = [r for r in groups["US-Iran peace deal"] if "deal" in (r["title"] or "").lower() or "talks" in (r["title"] or "").lower() or "memorandum" in (r["title"] or "").lower() or "peace" in (r["title"] or "").lower()]

# 2. Venezuela earthquakes — subset: first reports across sources
groups["Venezuela earthquake first reports"] = [r for r in rows if "venezuela" in (r["title"] or "").lower() and "earthquake" in (r["title"] or "").lower()]
# Take first article per source
seen = {}
for r in groups["Venezuela earthquake first reports"]:
    if r["sn"] not in seen:
        seen[r["sn"]] = r
groups["Venezuela earthquake first reports"] = list(seen.values())

# 3. World Cup 2026 — across sources
groups["World Cup 2026 matches"] = [r for r in rows if "world cup" in (r["title"] or "").lower() and "2026" in (r["title"] or "").lower()]

# 4. Japan earthquake M7.2
groups["Japan M7.2 earthquake"] = find(["japan"], "earthquake")

# 5. Messi at World Cup 2026
groups["Messi World Cup 2026"] = find(["messi"])

# 6. Trump birthright citizenship SCOTUS
groups["Trump birthright citizenship"] = find(["birthright"])

# 7. SNAP benefits cuts
groups["SNAP benefits cuts"] = find(["snap"])

# 8. Sudan/Prairieland sentencing
groups["Prairieland zine sentencing"] = find(["prairieland"])

# 9. Israel-Hezbollah tensions
groups["Israel Hezbollah conflict"] = find(["israel"])  # too broad, filter
groups["Israel Hezbollah conflict"] = [r for r in groups["Israel Hezbollah conflict"] if "hezbollah" in (r["title"] or "").lower() or "gaza" in (r["title"] or "").lower() or "hamas" in (r["title"] or "").lower()]

# 10. China WTO/EU trade dispute
groups["China-EU trade dispute"] = find(["china"])
groups["China-EU trade dispute"] = [r for r in groups["China-EU trade dispute"] if "eu" in (r["title"] or "").lower() or "wto" in (r["title"] or "").lower() or "trade" in (r["title"] or "").lower()]

# 11. Taliban smartphone ban
groups["Taliban phone ban"] = find(["taliban"])
groups["Taliban phone ban"] = [r for r in groups["Taliban phone ban"] if "phone" in (r["title"] or "").lower() or "device" in (r["title"] or "").lower()]

# 12. Ukraine-Russia prisoner swap
groups["Ukraine-Russia POW swap"] = find(["ukraine"])
groups["Ukraine-Russia POW swap"] = [r for r in groups["Ukraine-Russia POW swap"] if "prisoner" in (r["title"] or "").lower() or "swap" in (r["title"] or "").lower() or "pow" in (r["title"] or "").lower()]

# 13. Heat wave / climate — Western Europe
groups["Western Europe heat wave"] = find(["heat"])
groups["Western Europe heat wave"] = [r for r in groups["Western Europe heat wave"] if "europe" in (r["title"] or "").lower() or "paris" in (r["title"] or "").lower() or "france" in (r["title"] or "").lower() or "temperature" in (r["title"] or "").lower()]

# 14. Milei Argentina politics
groups["Milei Argentina"] = find(["milei"])

# 15. Maradona trial
groups["Maradona trial"] = [r for r in rows if "maradona" in (r["title"] or "").lower()]

# Print all groups
for i, (name, arts) in enumerate(groups.items(), 1):
    group_report(f"{i}. {name}", arts)

conn.close()
