"""News article body cleaner — strips photo captions, credits, and location tags.

Phase 2 Y1: Tightened regex patterns anchored to line semantics.
- Lines ending with "(AP Photo/...)" or "(AP Video/...)" → removed entirely (photo captions)
- Lines with inline credits (Reuters, AP/, AFP, dpa) → credit stripped, content kept
- Location tags "WASHINGTON (AP) —" → stripped from line start
- Producer credits "Produced by Name" at line end → stripped
- Safety cap: if >30% of body removed, return original with warning
"""

import logging
import re

logger = logging.getLogger("narrative_nexus.cleaner")

# ── Pure photo caption lines (remove entirely) ───────────────────────────
# AP Photo/Video at end of line always means a photo caption — no real content.
#   "A man walks past a damaged building in Moron. (AP Photo/Name)"
#   "People at a fountain. (AP Photo/Alessandra Tarantino)"
_AP_PHOTO_LINE_RE = re.compile(
    r"\(AP\s*(?:Photo|Video)\s*/\s*[^)]+\)\s*$",
    re.IGNORECASE,
)

# ── Inline credit stripping (on content lines, keep the content) ─────────
# Credits that may appear on lines with real content:
#   "(AP/ Juan Arraez)"          → stripped
#   "(Reuters/Jane Doe)"          → stripped
#   "(AFP/Getty/Name)"            → stripped
#   "(dpa via AP)"                → stripped
_INLINE_CREDIT_RE = re.compile(
    r"\s*"
    r"\((?:"
    r"AP\s*/\s*[^)]+"
    r"|Reuters\s*/\s*[^)]+"
    r"|AFP\s*/\s*[^)]+"
    r"|dpa\s*(?:via\s*AP)?\s*/\s*[^)]+"
    r"|Getty\s*(?:via\s*AP)?\s*/\s*[^)]+"
    r")"
    r"\)",
    re.IGNORECASE,
)

# Y1a: Line-anchored producer credit
_PRODUCER_CREDIT_RE = re.compile(
    r"\.\s*Produced by\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*$",
)

# Y1a: Location tag at line start: "WASHINGTON (AP) —"
_LOCATION_TAG_RE = re.compile(
    r"^[A-Z][A-Z\s,]+(?:\s*\(AP\))?\s*[-–—]\s*",
)

# Y1c: Safety cap
MAX_REMOVAL_FRACTION = 0.30


def clean_body(body: str) -> tuple[str, bool]:
    """Strip boilerplate from news article body.

    Returns (cleaned_text, was_truncated_warning).
    """
    if not body:
        return "", False

    original_len = len(body)
    lines = body.split("\n")
    kept_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if kept_lines and kept_lines[-1] != "":
                kept_lines.append("")
            continue

        # Y1a: Remove lines that end with AP Photo/Video — these are photo captions
        if _AP_PHOTO_LINE_RE.search(stripped):
            continue

        # Strip inline credits from content lines
        cleaned = _INLINE_CREDIT_RE.sub("", stripped)

        # Strip producer credit at end of line
        cleaned = _PRODUCER_CREDIT_RE.sub(".", cleaned)

        # Strip location tag from line start
        cleaned = _LOCATION_TAG_RE.sub("", cleaned)

        cleaned = cleaned.strip()
        if cleaned:
            kept_lines.append(cleaned)

    # Collapse blank-line runs
    result_lines: list[str] = []
    for line in kept_lines:
        if line == "" and result_lines and result_lines[-1] == "":
            continue
        result_lines.append(line)

    result = "\n".join(result_lines).strip()

    # Y1c: Safety cap
    if original_len > 200:
        removed_frac = 1.0 - (len(result) / original_len)
        if removed_frac > MAX_REMOVAL_FRACTION:
            logger.warning(
                "cleaner removed %.0f%% of body (%d → %d chars) — returning original",
                removed_frac * 100, original_len, len(result),
            )
            return body, True

    return result, False


def get_embedding_input(title: str, body: str, max_body_chars: int = 1000) -> str:
    """Build the embedding input string: cleaned title + body[:N].

    Phase 2 Y2: body window increased from 200 to 1000 chars.
    Body is cleaned before truncation so the window captures actual content.
    """
    title_str = title or ""
    body_str = body or ""
    cleaned_body, _ = clean_body(body_str)
    body_window = cleaned_body[:max_body_chars]
    result = f"{title_str} {body_window}".strip()
    return result
