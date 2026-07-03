#!/usr/bin/env python3
"""Find more multi-source story groups for T4a."""
import sqlite3

conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

queries = {
    "Anthropic AI export ban": "%anthropic%",
    "Indonesia bank rate": "%indonesia%central%bank%",
    "Pakistan rescue": "%pakistan%rescue%",
    "Strait of Hormuz": "%hormuz%",
    "North Korea missile": "%north%korea%",
    "Argentina MSCI/inflation": "%argentina%msci%",
    "Lula Brazil": "%lula%brazil%",
    "Fentanyl opioid crisis": "%fentanyl%",
    "Nigeria election": "%nigeria%election%",
    "Ukraine drone attack": "%ukraine%drone%",
    "Gaza children genocide": "%gaza%child%",
    "Lebanon Hezbollah deal": "%lebanon%hezbollah%",
    "Soros OSF Indonesia": "%soros%",
    "Vietnam China": "%vietnam%china%",
    "Buttigieg false report": "%buttigieg%",
    "Maradona death trial": "%maradona%death%",
    "Russia Zaporozhye nuclear": "%zaporozhye%",
    "Taliban ban smartphones": "%taliban%smartphone%",
    "Prairieland zine sentence": "%prairieland%",
    "SpaceX China investors": "%spacex%china%",
}

for name, pattern in queries.items():
    rows = conn.execute("""
        SELECT a.id, a.title, s.name as sn
        FROM articles a JOIN sources s ON s.id = a.source_id
        WHERE a.title LIKE ? AND a.published_at >= '2026-06-01'
          AND a.body_status = 'AVAILABLE'
        ORDER BY a.published_at LIMIT 10
    """, (pattern,)).fetchall()
    srcs = {r["sn"] for r in rows}
    if len(srcs) >= 3:
        print(f"\n--- {name} ({len(srcs)} srcs, {len(rows)} arts)")
        for r in rows[:5]:
            print(f"  ID={r['id']} | {r['sn']} | {r['title'][:80]}")

conn.close()
