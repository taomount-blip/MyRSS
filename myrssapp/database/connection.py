"""SQLite connection manager (singleton pattern, thread-safe)."""

import sqlite3
import threading
from pathlib import Path
from typing import Optional


class DatabaseConnection:
    """Thread-safe singleton SQLite connection manager.

    Uses WAL journal mode for concurrent read access.
    Each thread gets its own connection via get_connection().
    """

    _instance: Optional["DatabaseConnection"] = None
    _lock = threading.Lock()

    def __new__(cls, db_path: Path | None = None) -> "DatabaseConnection":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Path | None = None):
        if self._initialized:
            return
        self._db_path: Path = db_path or Path(":memory:")
        self._local = threading.local()
        self._initialized = True

    @property
    def db_path(self) -> Path:
        return self._db_path

    def get_connection(self) -> sqlite3.Connection:
        """Return a thread-local SQLite connection.

        SQLite connections cannot be shared across threads.
        This method returns a separate connection per thread.
        """
        if not hasattr(self._local, "connection") or self._local.connection is None:
            conn = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.connection = conn
        return self._local.connection

    def close_all(self) -> None:
        """Close the thread-local connection if open."""
        if hasattr(self._local, "connection") and self._local.connection is not None:
            self._local.connection.close()
            self._local.connection = None

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (mainly for testing)."""
        with cls._lock:
            cls._instance = None
