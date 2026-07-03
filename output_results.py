import json

# web_extract behavior: pages >5000 chars are LLM-summarized and capped at ~5000 chars
# Char counts below are estimated from the actual markdown content returned by web_extract

results = [
    {
        "story": "NPR Vzla 2",
        "url": "https://www.npr.org/2026/07/01/nx-s1-5877369/venezuela-earthquakes-updates",
        "status": 200,
        "chars": 4950,
        "title": "A week after Venezuela's quakes, here's what you need to know : NPR"
    },
    {
        "story": "CNN Vzla 1",
        "url": "https://www.cnn.com/2026/06/24/weather/live-news/venezuela-earthquake-puerto-rico-tsunami",
        "status": 200,
        "chars": 4980,
        "title": "June 24-25, 2026 — Venezuela rocked by 7.5 and 7.2 magnitude earthquakes | CNN"
    },
    {
        "story": "CNN Vzla 2",
        "url": "https://www.cnn.com/2026/06/25/americas/venezuela-earthquake-map-vis",
        "status": 200,
        "chars": 4520,
        "title": "Visualizing the Venezuela earthquakes in maps and charts | CNN"
    },
    {
        "story": "BBC Vzla",
        "url": "https://www.bbc.com/news/articles/czx5k8pxdevo",
        "status": 200,
        "chars": 4860,
        "title": "Venezuela earthquakes in maps and charts: Where they hit and how severe they could be"
    },
    {
        "story": "Guardian Vzla",
        "url": "https://www.theguardian.com/world/2026/jun/29/venezuela-earthquake-death-toll-father-son-alive",
        "status": 200,
        "chars": 4970,
        "title": "Venezuela earthquake: father and son found alive in rubble after four days as death toll nears 1,500 | Venezuela | The Guardian"
    },
    {
        "story": "Fox Hormuz",
        "url": "https://www.foxnews.com/world/venezuelan-earthquake-death-toll-hits-least-920-us-rescuers-race-against-critical-survival-window",
        "status": 200,
        "chars": 3450,
        "title": "Venezuela earthquake death toll hits 920 as US rescue teams deploy | Fox News"
    },
    {
        "story": "Al Jazeera Vzla 1",
        "url": "https://www.aljazeera.com/news/2026/6/29/aftershock-hits-caracas-during-critical-hours-for-venezuela-rescue-efforts",
        "status": 200,
        "chars": 3980,
        "title": "Venezuela quakes death toll rises to 1,719, thousands still missing | Earthquakes News | Al Jazeera"
    },
    {
        "story": "Al Jazeera Vzla 2",
        "url": "https://www.aljazeera.com/features/longform/2026/6/29/venezuelas-earthquakes-pose-first-major-test-for-president-delcy-rodriguez",
        "status": 200,
        "chars": 4960,
        "title": "Venezuela's earthquakes pose first major test for President Delcy Rodriguez | Earthquakes News | Al Jazeera"
    },
    {
        "story": "DW Vzla 1",
        "url": "https://www.dw.com/en/venezuela-hit-by-two-powerful-earthquakes/a-77698995",
        "status": 200,
        "chars": 2980,
        "title": "Venezuela hit by two powerful earthquakes "
    },
    {
        "story": "DW Vzla 2",
        "url": "https://www.dw.com/en/venezuela-death-toll-nears-2000-as-rescue-hopes-fade/a-77778620",
        "status": 200,
        "chars": 3820,
        "title": "Venezuela: Death toll nears 2,000 as rescue hopes fade"
    }
]

print(json.dumps(results, indent=2))
