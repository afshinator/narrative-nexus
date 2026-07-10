#!/usr/bin/env bash
set -euo pipefail
eval "KEY=\$FIREWORKS_API_KEY"
if [ -z "$KEY" ]; then echo "ERROR: FIREWORKS_API_KEY not set"; exit 1; fi
curl -s -H "Authorization: Bearer $KEY" \
  "https://api.fireworks.ai/v1/accounts/afshinator-b1hiwmnhr/deployments" | \
  python3 -c 'import sys,json;d=json.load(sys.stdin);[print(dep.get("displayName","?"),dep.get("state","?")) for dep in d.get("deployments",[])] or print("No deployments found")'
