"""RSS fetching and parsing service using requests + feedparser."""

import logging
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from ..database.connection import DatabaseConnection
from ..models.article import Article
from ..models.feed import Feed

logger = logging.getLogger(__name__)


class ParsedFeed:
    """Result of parsing an RSS feed URL."""

    def __init__(self):
        self.title: str = ""
        self.site_url: str = ""
        self.description: str = ""
        self.articles: list[Article] = []


class FetchService:
    """Downloads and parses RSS/Atom feeds, bulk-inserts articles."""

    REQUEST_TIMEOUT = 15
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self, db: DatabaseConnection):
        self._db = db

    def fetch_and_parse(self, url: str) -> Optional[ParsedFeed]:
        """Download and parse a single RSS/Atom feed URL.

        Returns None on network/parse failure.
        """
        try:
            resp = requests.get(
                url,
                timeout=self.REQUEST_TIMEOUT,
                headers={"User-Agent": self.USER_AGENT},
                allow_redirects=True,
            )
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
        except requests.RequestException as e:
            logger.warning("Failed to fetch %s: %s", url, e)
            return None

        parsed = feedparser.parse(resp.content)
        if parsed.bozo and not parsed.entries:
            logger.warning("Feedparser error for %s: %s", url, parsed.bozo_exception)
            return None

        result = ParsedFeed()
        result.title = parsed.feed.get("title", urlparse(url).netloc)
        result.site_url = parsed.feed.get("link", "")
        result.description = parsed.feed.get("subtitle", "") or parsed.feed.get("description", "")

        for entry in parsed.entries:
            guid = entry.get("id") or entry.get("link") or hashlib.md5(
                (entry.get("title", "") + entry.get("link", "")).encode()
            ).hexdigest()

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(
                        *entry.published_parsed[:6], tzinfo=timezone.utc
                    ).isoformat()
                except (TypeError, ValueError):
                    pass

            # Extract content preferring full content over summary
            content = ""
            if hasattr(entry, "content") and entry.content:
                content = entry.content[0].get("value", "")
            if not content and hasattr(entry, "summary"):
                content = entry.get("summary", "")

            summary = entry.get("summary", "") or ""
            if summary:
                # Strip HTML from summary for preview
                soup = BeautifulSoup(summary, "html.parser")
                summary = soup.get_text(separator=" ", strip=True)[:500]

            article = Article(
                feed_id=0,
                guid=guid,
                title=entry.get("title", "(无标题)"),
                link=entry.get("link", ""),
                author=entry.get("author", ""),
                summary=summary,
                content=content,
                published_at=published,
            )
            result.articles.append(article)

        return result

    def fetch_feed(self, feed: Feed) -> int:
        """Fetch a feed and bulk-insert new articles. Returns count of new articles."""
        parsed = self.fetch_and_parse(feed.url)
        if parsed is None:
            return 0

        # Update feed metadata
        from ..services.feed_service import FeedService
        feed_svc = FeedService(self._db)
        feed_svc.update_feed_info(
            feed.id, parsed.title, parsed.site_url, parsed.description
        )

        # Insert articles (skip duplicates via INSERT OR IGNORE)
        new_count = 0
        conn = self._db.get_connection()
        for article in parsed.articles:
            article.feed_id = feed.id
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO articles "
                    "(feed_id, guid, title, link, author, summary, content, published_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        article.feed_id, article.guid, article.title,
                        article.link, article.author, article.summary,
                        article.content, article.published_at,
                    ),
                )
                if conn.changes > 0:
                    new_count += 1
            except Exception:
                continue

        conn.commit()

        # Enforce per-feed article limit
        self._enforce_article_limit(feed.id)

        # Reset error state on success
        feed_svc.reset_feed_error(feed.id)
        feed_svc.update_last_fetched(feed.id)

        return new_count

    def fetch_all_active(self) -> dict[int, int]:
        """Fetch all active feeds concurrently. Returns {feed_id: new_article_count}."""
        from ..services.feed_service import FeedService
        feed_svc = FeedService(self._db)
        feeds = feed_svc.get_all_feeds()

        results: dict[int, int] = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_map = {executor.submit(self.fetch_feed, f): f.id for f in feeds}
            for future in as_completed(future_map):
                feed_id = future_map[future]
                try:
                    results[feed_id] = future.result()
                except Exception as e:
                    logger.exception("Unexpected error fetching feed %d", feed_id)
                    results[feed_id] = 0
        return results

    def fetch_feed_only(self, url: str) -> Optional[ParsedFeed]:
        """Fetch and parse a feed without inserting articles. Used for preview."""
        return self.fetch_and_parse(url)

    def _enforce_article_limit(self, feed_id: int) -> None:
        """Delete oldest articles if exceeding max_articles_per_feed."""
        from ..services.settings_service import SettingsService
        settings = SettingsService(self._db)
        max_articles = settings.max_articles_per_feed

        conn = self._db.get_connection()
        conn.execute(
            "DELETE FROM articles WHERE id IN ("
            "  SELECT id FROM articles WHERE feed_id = ? "
            "  ORDER BY published_at DESC "
            "  LIMIT -1 OFFSET ?"
            ")",
            (feed_id, max_articles),
        )
        conn.commit()
