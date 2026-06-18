"""Generic Repository pattern for SQLite data access."""

from __future__ import annotations

import sqlite3
from typing import Any, Generic, Optional, TypeVar, get_type_hints

from ..database.connection import DatabaseConnection

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic CRUD repository for a dataclass-backed SQLite table.

    Subclasses must define:
        table_name: str
        model_class: type[T]
        columns: list[str]  (excluding auto-increment id)
    """

    table_name: str = ""
    model_class: type[T] = None  # type: ignore[assignment]
    columns: list[str] = []

    def __init__(self, db: DatabaseConnection):
        self._db = db

    @property
    def _conn(self) -> sqlite3.Connection:
        return self._db.get_connection()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _row_to_model(self, row: sqlite3.Row) -> T:
        """Convert a sqlite3.Row to the model dataclass."""
        kwargs = dict(row)
        # Convert integer booleans back to Python bool
        hints = get_type_hints(self.model_class)
        for key, val in kwargs.items():
            if key in hints and hints[key] is bool:
                kwargs[key] = bool(val)
        return self.model_class(**kwargs)

    def _quote_cols(self) -> str:
        return ", ".join(self.columns)

    def _quote_placeholders(self) -> str:
        return ", ".join("?" for _ in self.columns)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def get_by_id(self, entity_id: int) -> Optional[T]:
        row = self._conn.execute(
            f"SELECT * FROM {self.table_name} WHERE id = ?", (entity_id,)
        ).fetchone()
        return self._row_to_model(row) if row else None

    def get_all(self, order_by: str = "id ASC") -> list[T]:
        rows = self._conn.execute(
            f"SELECT * FROM {self.table_name} ORDER BY {order_by}"
        ).fetchall()
        return [self._row_to_model(r) for r in rows]

    def create(self, entity: T) -> int:
        values = [getattr(entity, col) for col in self.columns]
        cursor = self._conn.execute(
            f"INSERT INTO {self.table_name} ({self._quote_cols()}) "
            f"VALUES ({self._quote_placeholders()})",
            values,
        )
        self._conn.commit()
        entity.id = cursor.lastrowid
        return cursor.lastrowid

    def update(self, entity: T) -> bool:
        if entity.id is None:
            return False
        set_clause = ", ".join(f"{col} = ?" for col in self.columns)
        values = [getattr(entity, col) for col in self.columns] + [entity.id]
        self._conn.execute(
            f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?",
            values,
        )
        self._conn.commit()
        return True

    def delete(self, entity_id: int) -> bool:
        self._conn.execute(
            f"DELETE FROM {self.table_name} WHERE id = ?", (entity_id,)
        )
        self._conn.commit()
        return True

    def count(self, where_clause: str = "", params: tuple = ()) -> int:
        sql = f"SELECT COUNT(*) FROM {self.table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        row = self._conn.execute(sql, params).fetchone()
        return row[0] if row else 0

    def exists(self, where_clause: str, params: tuple) -> bool:
        return self.count(where_clause, params) > 0
