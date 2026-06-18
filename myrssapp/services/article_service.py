"""Article service – query, search, mark read/favorite."""

from typing import Optional

from ..database.connection import DatabaseConnection
from ..models.article import Article


class ArticleService:
    """Manages article queries and status changes."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------
    def get_article(self, article_id: int) -> Optional[Article]:
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT a.*, f.title AS feed_title "
            "FROM articles a JOIN feeds f ON a.feed_id = f.id "
            "WHERE a.id = ?",
            (article_id,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_article(row)

    def get_articles(
        self,
        feed_id: Optional[int] = None,
        category_id: Optional[int] = None,
        is_read: Optional[bool] = None,
        is_favorited: Optional[bool] = None,
        search_keyword: str = "",
        sort_order: str = "published_at DESC",
        limit: int = 100,
        offset: int = 0,
    ) -> list[Article]:
        """Flexible article query with multiple filter options."""
        conn = self._db.get_connection()

        conditions = []
        params: list = []

        if feed_id is not None:
            conditions.append("a.feed_id = ?")
            params.append(feed_id)
        elif category_id is not None:
            conditions.append("f.category_id = ?")
            params.append(category_id)

        if is_read is not None:
            conditions.append("a.is_read = ?")
            params.append(int(is_read))

        if is_favorited is not None:
            conditions.append("a.is_favorited = ?")
            params.append(int(is_favorited))

        if search_keyword.strip():
            conditions.append(
                "a.id IN (SELECT rowid FROM articles_fts WHERE articles_fts MATCH ?)"
            )
            params.append(search_keyword)

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        # Security: only whitelisted sort columns
        sort_map = {
            "published_at DESC": "a.published_at DESC",
            "published_at ASC": "a.published_at ASC",
            "title ASC": "a.title ASC",
        }
        order = sort_map.get(sort_order, "a.published_at DESC")

        sql = (
            f"SELECT a.*, f.title AS feed_title "
            f"FROM articles a JOIN feeds f ON a.feed_id = f.id "
            f"{where} ORDER BY {order} LIMIT ? OFFSET ?"
        )
        params.extend([limit, offset])

        rows = conn.execute(sql, params).fetchall()
        return [self._row_to_article(r) for r in rows]

    def get_article_count(
        self,
        feed_id: Optional[int] = None,
        category_id: Optional[int] = None,
        is_read: Optional[bool] = None,
        is_favorited: Optional[bool] = None,
        search_keyword: str = "",
    ) -> int:
        """Return total count matching filters (for pagination)."""
        conn = self._db.get_connection()

        conditions = []
        params: list = []

        if feed_id is not None:
            conditions.append("a.feed_id = ?")
            params.append(feed_id)
        elif category_id is not None:
            conditions.append("f.category_id = ?")
            params.append(category_id)

        if is_read is not None:
            conditions.append("a.is_read = ?")
            params.append(int(is_read))

        if is_favorited is not None:
            conditions.append("a.is_favorited = ?")
            params.append(int(is_favorited))

        if search_keyword.strip():
            conditions.append(
                "a.id IN (SELECT rowid FROM articles_fts WHERE articles_fts MATCH ?)"
            )
            params.append(search_keyword)

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        row = conn.execute(
            f"SELECT COUNT(*) FROM articles a JOIN feeds f ON a.feed_id = f.id {where}",
            params,
        ).fetchone()
        return row[0] if row else 0

    def get_total_unread_count(self, feed_id: Optional[int] = None) -> int:
        conn = self._db.get_connection()
        if feed_id:
            row = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE feed_id = ? AND is_read = 0",
                (feed_id,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE is_read = 0"
            ).fetchone()
        return row[0] if row else 0

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    def mark_read(self, article_id: int) -> None:
        conn = self._db.get_connection()
        conn.execute(
            "UPDATE articles SET is_read = 1 WHERE id = ?", (article_id,)
        )
        conn.commit()

    def mark_unread(self, article_id: int) -> None:
        conn = self._db.get_connection()
        conn.execute(
            "UPDATE articles SET is_read = 0 WHERE id = ?", (article_id,)
        )
        conn.commit()

    def mark_all_read(self, feed_id: Optional[int] = None) -> int:
        """Mark all unread articles as read. Returns count of affected rows."""
        conn = self._db.get_connection()
        if feed_id:
            conn.execute(
                "UPDATE articles SET is_read = 1 WHERE feed_id = ? AND is_read = 0",
                (feed_id,),
            )
        else:
            conn.execute("UPDATE articles SET is_read = 1 WHERE is_read = 0")
        conn.commit()
        return conn.changes

    def toggle_favorite(self, article_id: int) -> bool:
        """Toggle favorite status. Returns new favorited state."""
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT is_favorited FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        if not row:
            return False
        new_val = 0 if row["is_favorited"] else 1
        conn.execute(
            "UPDATE articles SET is_favorited = ? WHERE id = ?", (new_val, article_id)
        )
        conn.commit()
        return bool(new_val)

    def delete_article(self, article_id: int) -> None:
        conn = self._db.get_connection()
        conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        conn.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_article(row) -> Article:
        return Article(
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
