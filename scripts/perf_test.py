#!/usr/bin/env python3
"""Measure page load performance by timing HTTP requests and analyzing chunk sizes.
Tests both initial load and subsequent navigation (cached chunks).
"""
import time
import urllib.request
import re
import sys
from concurrent.futures import ThreadPoolExecutor

BASE = "http://localhost:3015"

def fetch(url: str) -> tuple[str, int, float]:
    """Fetch URL, return (body, status, elapsed_seconds)."""
    t0 = time.time()
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return body, resp.status, time.time() - t0
    except Exception as e:
        return "", 0, time.time() - t0

def get_chunk_urls(html: str) -> list[str]:
    """Extract JS chunk URLs from index.html."""
    urls = re.findall(r'src="(/assets/[^"]+)"', html)
    css = re.findall(r'href="(/assets/[^"]+\.css)"', html)
    return urls + css

# ── Phase 1: Initial page load ────────────────────────────────────────
print("=== Phase 1: Initial page load (uncached) ===")
_, _, html_time = fetch(BASE)
print(f"  index.html: {html_time*1000:.0f}ms")

html, _, _ = fetch(BASE)
chunks = get_chunk_urls(html)
print(f"  Chunks to load: {len(chunks)}")

total_size = 0
total_time = 0
for url in chunks:
    full_url = f"{BASE}{url}"
    body, status, elapsed = fetch(full_url)
    size = len(body.encode())
    total_size += size
    total_time += elapsed
    name = url.split("/")[-1][:30]
    print(f"  {name:35s} {size:>8,}B  {elapsed*1000:>5.0f}ms")

print(f"  TOTAL: {total_size:,}B ({total_size/1024:.0f}KB) in {total_time*1000:.0f}ms")


# ── Phase 2: Simulate navigation to each page ─────────────────────────
print("\n=== Phase 2: Page chunk sizes (simulated navigation) ===")

# Pages and their chunk file name patterns
pages = {
    "/": "Sources",
    "/settings": "Settings",
    "/panel": "Panel",
    "/pipeline": "PipelineFlow",
    "/cluster/880": "ClusterReport",
    "/investigate": "Investigate",
    "/source/reuters.com": "SourceProfile",
}

# Check if each page has a separate chunk
import os
dist_assets = "/project/narrative-nexus/dist/assets"

for path, name in pages.items():
    chunk_files = [f for f in os.listdir(dist_assets) if f.startswith(name) and f.endswith(".js")]
    if chunk_files:
        size = os.path.getsize(os.path.join(dist_assets, chunk_files[0]))
        # Check if this page depends on d3 or chartjs
        deps = []
        chunk_content = open(os.path.join(dist_assets, chunk_files[0])).read()
        if "d3" in chunk_content.lower() or "symbolCircle" in chunk_content:
            deps.append("d3 (53KB)")
        if "chart.js" in chunk_content.lower() or "ChartJS" in chunk_content:
            deps.append("chartjs (179KB)")

        dep_list = " + ".join(deps) if deps else "none"
        print(f"  {path:25s} {size:>6,}B  deps: {dep_list}")
    else:
        print(f"  {path:25s} (in main bundle)")

# ── Phase 3: API response times ───────────────────────────────────────
print("\n=== Phase 3: API response times (backend) ===")

apis = {
    "/api/scores": "Scores (37 sources)",
    "/api/clusters/880/report": "Cluster 880 report",
    "/api/sources/1/profile?vertical=geopolitics": "Source profile (180 days)",
    "/api/sources": "Sources list",
}

for url, label in apis.items():
    _, status, elapsed = fetch(f"http://localhost:3006{url}")
    print(f"  {label:35s} {elapsed*1000:>5.0f}ms  status={status}")


# ── Summary ───────────────────────────────────────────────────────────
print("\n=== Analysis ===")
print("If API times are <100ms but navigation feels slow (>1s):")
print("  → Main-thread blocked during React mount/unmount")
print("  → Check: Chart.js destroy() on unmount, D3 cleanup, CSS recalculation")
print("If API times are >500ms:")
print("  → Backend bottleneck — needs query optimization or caching")
