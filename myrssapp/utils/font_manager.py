"""Font settings manager."""

from PySide6.QtCore import QObject


class FontManager(QObject):
    """Manages application font settings."""

    def __init__(self):
        super().__init__()
        self._font_family = "Microsoft YaHei"
        self._font_size = 16

    @property
    def font_family(self) -> str:
        return self._font_family

    @font_family.setter
    def font_family(self, value: str) -> None:
        self._font_family = value

    @property
    def font_size(self) -> int:
        return self._font_size

    @font_size.setter
    def font_size(self, value: int) -> None:
        self._font_size = max(10, min(48, value))
