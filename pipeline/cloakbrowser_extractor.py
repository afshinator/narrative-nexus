"""CloakBrowser extractor — resolves Google News redirect URLs via stealth Chromium."""
import json
import subprocess
from pathlib import Path

_BRIDGE = Path(__file__).resolve().parent / "cloakbrowser_bridge.mjs"


def extract(url: str, timeout: int = 20) -> tuple[str | None, str]:
    """Resolve a URL through CloakBrowser and extract visible text.

    Returns (body_text, body_status) — AVAILABLE if text was extracted,
    BODY_UNAVAILABLE if the extraction failed or returned empty.
    """
    try:
        result = subprocess.run(
            ["node", str(_BRIDGE), url],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        data = json.loads(result.stdout.strip())
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as exc:
        return None, "BODY_UNAVAILABLE"

    if "error" in data or not data.get("text"):
        return None, "BODY_UNAVAILABLE"

    # Only accept text if it's substantial (more than just navigation boilerplate)
    text = data["text"]
    if len(text) < 80:
        return None, "BODY_UNAVAILABLE"

    return text, "AVAILABLE"
