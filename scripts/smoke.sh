#!/usr/bin/env bash
# Narrative Nexus — container rebuild + smoke test
# Run from repo root on the host. Exits nonzero on first failure.
set -euo pipefail

EXPECT_ARTICLES=358
EXPECT_SOURCES=37
HOST_DB="data/demo/demo.db"

echo "== 0. Host DB fingerprint (before) =="
python3 - <<EOF
import sqlite3
db = sqlite3.connect("$HOST_DB")
counts = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
          for t in ["claims","articles","clusters","snapshots"]}
counts["absorbed"] = db.execute(
    "SELECT COUNT(*) FROM claims WHERE state='CONSENSUS_ABSORBED'").fetchone()[0]
print(counts)
assert counts == {"claims":378,"articles":358,"clusters":17,
                  "snapshots":13653,"absorbed":10}, "HOST DB FINGERPRINT MISMATCH"
EOF

echo "== 1. Down, rebuild, up =="
docker compose down
docker compose build app
docker compose up -d

echo "== 2. Wait for app on :8000 =="
for i in $(seq 1 30); do
  curl -sf http://localhost:8000/api/stats >/dev/null 2>&1 && break
  sleep 1
  [ "$i" -eq 30 ] && { echo "FAIL: app not up after 30s"; docker compose logs app | tail -30; exit 1; }
done

echo "== 3. /api/stats =="
STATS=$(curl -s http://localhost:8000/api/stats)
echo "$STATS"
echo "$STATS" | python3 -c "
import sys, json
s = json.load(sys.stdin)
assert s['articles'] == $EXPECT_ARTICLES, f\"articles={s['articles']}, expected $EXPECT_ARTICLES\"
assert s['sources'] == $EXPECT_SOURCES, f\"sources={s['sources']}, expected $EXPECT_SOURCES\"
print('PASS: stats match')
"

echo "== 4. SPA served =="
curl -s http://localhost:8000/ | head -3
curl -s http://localhost:8000/ | grep -qi "<!doctype html" && echo "PASS: SPA HTML" || { echo "FAIL: no HTML"; exit 1; }

echo "== 5. In-container DB fingerprint =="
docker compose exec -T app python3 -c "
import sqlite3
db = sqlite3.connect('/data/demo/demo.db')
counts = {t: db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
          for t in ['claims','articles','clusters','snapshots']}
counts['absorbed'] = db.execute(\"SELECT COUNT(*) FROM claims WHERE state='CONSENSUS_ABSORBED'\").fetchone()[0]
print(counts)
assert counts == {'claims':378,'articles':358,'clusters':17,'snapshots':13653,'absorbed':10}, 'IN-CONTAINER FINGERPRINT MISMATCH'
print('PASS: container DB is golden copy')
"

echo "== 6. Host DB fingerprint (after) — container must not touch it =="
python3 - <<EOF
import sqlite3
db = sqlite3.connect("$HOST_DB")
c = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
assert c == 358, f"HOST DB MUTATED: articles={c}"
print("PASS: host DB untouched")
EOF

echo ""
echo "ALL PASS. Container is up at http://localhost:8000"
echo "Manual steps remaining:"
echo "  - Browser: Sources scatter, source profile radar, Cluster Report, timeline 966"
echo "  - Settings -> Start scraper (keyless) — observe and record behavior"
echo "  - When done: docker compose down"