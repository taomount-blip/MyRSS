"""Full-text search service using SQLite FTS5."""

import re
from typing import Optional

from ..database.connection import DatabaseConnection
from ..models.article import Article


class SearchService:
    """Performs FTS5 full-text search on articles."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    def search(
        self,
        query: str,
        feed_id: Optional[int] = None,
        limit: int = 50,
    ) -> list[Article]:
        """Search articles via FTS5 MATCH query.

        Simple query sanitization: strip special FTS syntax characters
        unless the user explicitly uses them.
        """
        if not query.strip():
            return []

        conn = self._db.get_connection()

        # Sanitize: escape special chars but allow quoted phrases
        safe_query = self._sanitize_query(query)
        fts_condition = "a.id IN (SELECT rowid FROM articles_fts WHERE articles_fts MATCH ?)"

        params: list = [safe_query]
        where_extra = ""
        if feed_id is not None:
            where_extra = " AND a.feed_id = ?"
            params.append(feed_id)

        sql = (
            "SELECT a.*, f.title AS feed_title, "
            "snippet(articles_fts, 1, '<mark>', '</mark>', '...', 40) AS snippet "
            "FROM articles a JOIN feeds f ON a.feed_id = f.id "
            f"WHERE {fts_condition}{where_extra} "
            "ORDER BY rank LIMIT ?"
        )
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        return [self._row_to_article_with_snippet(r) for r in rows]

    def get_snippet(self, article_id: int, query: str) -> str:
        """Return a highlighted snippet for an article matching the query."""
        conn = self._db.get_connection()
        safe_query = self._sanitize_query(query)
        row = conn.execute(
            "SELECT snippet(articles_fts, 1, '<mark>', '</mark>', '...', 40) AS snippet "
            "FROM articles_fts WHERE rowid = ? AND articles_fts MATCH ?",
            (article_id, safe_query),
        ).fetchone()
        if row and row["snippet"]:
            return row["snippet"]
        return ""

    def index_article(self, article_id: int) -> None:
        """Explicitly re-index an article. Normally handled by triggers."""
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT title, content, summary FROM articles WHERE id = ?",
            (article_id,),
        ).fetchone()
        if row:
            # Trigger-based update handles this automatically,
            # but we provide this for edge cases.
            conn.execute(
                "UPDATE articles SET title = title WHERE id = ?", (article_id,)
            )
            conn.commit()

    @staticmethod
    def _sanitize_query(query: str) -> str:
        """Sanitize user query for FTS5. Allow quoted phrases and basic operators."""
        # If the user typed a quoted phrase, trust it
        if query.startswith('"') and query.endswith('"'):
            return query

        # Escape FTS5 special characters
        # FTS5 special chars: * " - + ( ) [ ] { } ~ ^
        special_chars = r'([*\-+()\[\]{}~^])'
        sanitized = re.sub(special_chars, r'\\\1', query)

        # Add prefix matching for the last word (unless there are spaces at end)
        if sanitized and not sanitized.endswith(("*", " ")):
            sanitized = sanitized + "*"

        return sanitized

    @staticmethod
    def _row_to_article_with_snippet(row) -> Article:
        article = Article(
            id=row["id"],
            feed_id=row["feed_id"],
            guid=row["guid"],
            title=row["title"],
            link=row["link"],
            author=row["author"] or "",
            summary=row["summary"] or "",
            content=row["content"] or "",
            published_at=row["published_at"],
            fetched_at=row["fetched_at"],
            is_read=bool(row["is_read"]),
            is_favorited=bool(row["is_favorited"]),
            created_at=row["created_at"],
            feed_title=row["feed_title"] or "",
        )
        return article
