"""Theme manager for loading and switching QSS stylesheets."""

from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication


class ThemeManager(QObject):
    """Manages application themes (light/dark) via QSS stylesheets."""

    def __init__(self, styles_dir: Path):
        super().__init__()
        self._styles_dir = Path(styles_dir)
        self._current_theme = "light"
        self._base_qss = ""
        self._theme_qss = ""

    def load_base(self) -> None:
        """Load the base stylesheet shared across themes."""
        base_path = self._styles_dir / "base.qss"
        if base_path.exists():
            self._base_qss = base_path.read_text(encoding="utf-8")

    def apply_theme(self, theme: str) -> None:
        """Apply a theme by name (light / dark)."""
        self._current_theme = theme
        theme_path = self._styles_dir / f"{theme}.qss"

        if theme_path.exists():
            self._theme_qss = theme_path.read_text(encoding="utf-8")

        QApplication.instance().setStyleSheet(self._base_qss + "\n" + self._theme_qss)

    @property
    def current_theme(self) -> str:
        return self._current_theme
