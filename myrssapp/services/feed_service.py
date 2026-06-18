"""Feed service – CRUD operations on RSS subscriptions."""

from typing import Optional

from ..database.connection import DatabaseConnection
from ..models.feed import Feed
from ..models.category import Category


class FeedService:
    """Manages feed subscriptions and their associated categories."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    # ------------------------------------------------------------------
    # Feed CRUD
    # ------------------------------------------------------------------
    def add_feed(self, url: str, category_id: Optional[int] = None) -> Feed:
        """Create a new feed subscription. URL must be unique."""
        conn = self._db.get_connection()
        cursor = conn.execute(
            "INSERT INTO feeds (url, title, category_id) VALUES (?, ?, ?)",
            (url, url, category_id),
        )
        conn.commit()
        feed_id = cursor.lastrowid
        return self.get_feed(feed_id)  # type: ignore[return-value]

    def get_feed(self, feed_id: int) -> Optional[Feed]:
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT f.*, "
            "(SELECT COUNT(*) FROM articles a WHERE a.feed_id = f.id AND a.is_read = 0) AS unread_count, "
            "(SELECT COUNT(*) FROM articles a WHERE a.feed_id = f.id) AS total_count "
            "FROM feeds f WHERE f.id = ?",
            (feed_id,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_feed(row)

    def get_feed_by_url(self, url: str) -> Optional[Feed]:
        conn = self._db.get_connection()
        row = conn.execute("SELECT * FROM feeds WHERE url = ?", (url,)).fetchone()
        if not row:
            return None
        return self._row_to_feed(row)

    def get_all_feeds(self, include_disabled: bool = False) -> list[Feed]:
        conn = self._db.get_connection()
        where = "" if include_disabled else "WHERE f.is_active = 1"
        rows = conn.execute(
            f"SELECT f.*, "
            "(SELECT COUNT(*) FROM articles a WHERE a.feed_id = f.id AND a.is_read = 0) AS unread_count, "
            "(SELECT COUNT(*) FROM articles a WHERE a.feed_id = f.id) AS total_count "
            f"FROM feeds f {where} ORDER BY f.title ASC"
        ).fetchall()
        return [self._row_to_feed(r) for r in rows]

    def get_feeds_by_category(self, category_id: int) -> list[Feed]:
        conn = self._db.get_connection()
        rows = conn.execute(
            "SELECT f.*, "
            "(SELECT COUNT(*) FROM articles a WHERE a.feed_id = f.id AND a.is_read = 0) AS unread_count, "
            "(SELECT COUNT(*) FROM articles a WHERE a.feed_id = f.id) AS total_count "
            "FROM feeds f WHERE f.category_id = ? AND f.is_active = 1 ORDER BY f.title",
            (category_id,),
        ).fetchall()
        return [self._row_to_feed(r) for r in rows]

    def update_feed(self, feed: Feed) -> None:
        conn = self._db.get_connection()
        conn.execute(
            "UPDATE feeds SET title=?, url=?, site_url=?, description=?, icon_path=?, "
            "update_interval=?, category_id=?, is_active=?, "
            "last_fetched_at=?, error_count=?, last_error=?, updated_at=datetime('now') "
            "WHERE id=?",
            (
                feed.title, feed.url, feed.site_url, feed.description, feed.icon_path,
                feed.update_interval, feed.category_id, int(feed.is_active),
                feed.last_fetched_at, feed.error_count, feed.last_error,
                feed.id,
            ),
        )
        conn.commit()

    def update_feed_info(self, feed_id: int, title: str, site_url: str,
                         description: str) -> None:
        conn = self._db.get_connection()
        conn.execute(
            "UPDATE feeds SET title=?, site_url=?, description=?, updated_at=datetime('now') "
            "WHERE id=?",
            (title, site_url, description, feed_id),
        )
        conn.commit()

    def update_feed_error(self, feed_id: int, error: str) -> None:
        conn = self._db.get_connection()
        conn.execute(
            "UPDATE feeds SET error_count = error_count + 1, last_error = ?, updated_at = datetime('now') "
            "WHERE id = ?",
            (error, feed_id),
        )
        conn.commit()

    def reset_feed_error(self, feed_id: int) -> None:
        conn = self._db.get_connection()
        conn.execute(
            "UPDATE feeds SET error_count = 0, last_error = '', updated_at = datetime('now') "
            "WHERE id = ?",
            (feed_id,),
        )
        conn.commit()

    def update_last_fetched(self, feed_id: int) -> None:
        conn = self._db.get_connection()
        conn.execute(
            "UPDATE feeds SET last_fetched_at = datetime('now'), updated_at = datetime('now') "
            "WHERE id = ?",
            (feed_id,),
        )
        conn.commit()

    def delete_feed(self, feed_id: int) -> None:
        """Delete a feed and all its articles (CASCADE)."""
        conn = self._db.get_connection()
        conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
        conn.commit()

    # ------------------------------------------------------------------
    # Category CRUD
    # ------------------------------------------------------------------
    def add_category(self, name: str) -> Category:
        conn = self._db.get_connection()
        cursor = conn.execute(
            "INSERT INTO categories (name) VALUES (?)", (name,)
        )
        conn.commit()
        return self.get_category(cursor.lastrowid)  # type: ignore[return-value]

    def get_category(self, category_id: int) -> Optional[Category]:
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT c.*, "
            "(SELECT COUNT(*) FROM feeds f WHERE f.category_id = c.id) AS feed_count, "
            "(SELECT COUNT(*) FROM articles a "
            " JOIN feeds f ON a.feed_id = f.id "
            " WHERE f.category_id = c.id AND a.is_read = 0) AS unread_count "
            "FROM categories c WHERE c.id = ?",
            (category_id,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_category(row)

    def get_all_categories(self) -> list[Category]:
        conn = self._db.get_connection()
        rows = conn.execute(
            "SELECT c.*, "
            "(SELECT COUNT(*) FROM feeds f WHERE f.category_id = c.id) AS feed_count, "
            "(SELECT COUNT(*) FROM articles a "
            " JOIN feeds f ON a.feed_id = f.id "
            " WHERE f.category_id = c.id AND a.is_read = 0) AS unread_count "
            "FROM categories c ORDER BY c.sort_order, c.name"
        ).fetchall()
        return [self._row_to_category(r) for r in rows]

    def update_category(self, category: Category) -> None:
        conn = self._db.get_connection()
        conn.execute(
            "UPDATE categories SET name=?, description=?, icon=?, sort_order=?, "
            "updated_at=datetime('now') WHERE id=?",
            (category.name, category.description, category.icon,
             category.sort_order, category.id),
        )
        conn.commit()

    def delete_category(self, category_id: int) -> None:
        conn = self._db.get_connection()
        # Set category_id to NULL for feeds in this category
        conn.execute(
            "UPDATE feeds SET category_id = NULL WHERE category_id = ?",
            (category_id,),
        )
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_feed(row) -> Feed:
        return Feed(
            id=row["id"],
            category_id=row["category_id"],
            title=row["title"],
            url=row["url"],
            site_url=row["site_url"] or "",
            description=row["description"] or "",
            icon_path=row["icon_path"] or "",
            update_interval=row["update_interval"],
            last_fetched_at=row["last_fetched_at"],
            error_count=row["error_count"],
            last_error=row["last_error"] or "",
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            unread_count=row["unread_count"] or 0,
            total_count=row["total_count"] or 0,
        )

    @staticmethod
    def _row_to_category(row) -> Category:
        return Category(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            icon=row["icon"] or "",
            sort_order=row["sort_order"],
            feed_count=row["feed_count"] or 0,
            unread_count=row["unread_count"] or 0,
        )
