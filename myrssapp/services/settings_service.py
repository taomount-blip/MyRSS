"""Settings service – key-value configuration storage."""

from ..database.connection import DatabaseConnection
from ..models.settings_item import SettingsItem


class SettingsService:
    """Read and write application settings from the settings table."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    def get(self, key: str, default: str = "") -> str:
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        conn = self._db.get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) "
            "VALUES (?, ?, datetime('now'))",
            (key, value),
        )
        conn.commit()

    def get_all(self) -> list[SettingsItem]:
        conn = self._db.get_connection()
        rows = conn.execute("SELECT key, value, updated_at FROM settings").fetchall()
        return [
            SettingsItem(key=r["key"], value=r["value"], updated_at=r["updated_at"])
            for r in rows
        ]

    # -- Convenience accessors --

    @property
    def theme(self) -> str:
        return self.get("theme", "light")

    @theme.setter
    def theme(self, value: str) -> None:
        self.set("theme", value)

    @property
    def font_family(self) -> str:
        return self.get("font_family", "Microsoft YaHei")

    @font_family.setter
    def font_family(self, value: str) -> None:
        self.set("font_family", value)

    @property
    def font_size(self) -> int:
        return int(self.get("font_size", "16"))

    @font_size.setter
    def font_size(self, value: int) -> None:
        self.set("font_size", str(value))

    @property
    def update_interval(self) -> int:
        return int(self.get("update_interval", "3600"))

    @update_interval.setter
    def update_interval(self, value: int) -> None:
        self.set("update_interval", str(value))

    @property
    def max_articles_per_feed(self) -> int:
        return int(self.get("max_articles_per_feed", "200"))

    @property
    def translation_api_url(self) -> str:
        return self.get("translation_api_url", "")

    @property
    def translation_api_key(self) -> str:
        return self.get("translation_api_key", "")

    @property
    def translation_model(self) -> str:
        return self.get("translation_model", "hunyuan-lite")
