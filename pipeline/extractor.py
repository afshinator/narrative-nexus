"""Article body extraction via newspaper4k."""
from newspaper import Article, ArticleException
from newspaper.exceptions import ArticleBinaryDataException


class ArticleExtractor:
    """Downloads and extracts article body text. Best-effort — returns
    BODY_UNAVAILABLE on any failure (paywall, timeout, 404, binary data)."""

    def extract(self, url: str) -> tuple[str, str]:
        """Return (body_text, body_status). Status is AVAILABLE or BODY_UNAVAILABLE."""
        try:
            a = Article(url)
            a.download()
            a.parse()
            body = a.text or ""
            if len(body) > 0:
                return body, "AVAILABLE"
            return "", "BODY_UNAVAILABLE"
        except (ArticleException, ArticleBinaryDataException, OSError, ValueError):
            return "", "BODY_UNAVAILABLE"
