"""Settings ViewModel."""

from PySide6.QtCore import QObject, Signal, Property

from ..services.settings_service import SettingsService
from .base_viewmodel import BaseViewModel


class SettingsViewModel(BaseViewModel):
    """ViewModel for the Settings dialog."""

    settings_applied = Signal()

    def __init__(
        self,
        settings_service: SettingsService,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._settings = settings_service
        self._theme = "light"
        self._font_family = "Microsoft YaHei"
        self._font_size = 16
        self._update_interval = 3600
        self._translation_api_url = ""
        self._translation_api_key = ""
        self._translation_model = "hunyuan-lite"
        self.load()

    def load(self) -> None:
        self._theme = self._settings.theme
        self._font_family = self._settings.font_family
        self._font_size = self._settings.font_size
        self._update_interval = self._settings.update_interval
        self._translation_api_url = self._settings.translation_api_url
        self._translation_api_key = self._settings.translation_api_key
        self._translation_model = self._settings.translation_model

    def apply(self) -> None:
        self._settings.set("theme", self._theme)
        self._settings.set("font_family", self._font_family)
        self._settings.set("font_size", str(self._font_size))
        self._settings.set("update_interval", str(self._update_interval))
        self._settings.set("translation_api_url", self._translation_api_url)
        self._settings.set("translation_api_key", self._translation_api_key)
        self._settings.set("translation_model", self._translation_model)
        self.settings_applied.emit()

    def reset_defaults(self) -> None:
        self._theme = "light"
        self._font_family = "Microsoft YaHei"
        self._font_size = 16
        self._update_interval = 3600

    # Properties
    def _get_theme(self) -> str: return self._theme
    def _set_theme(self, v: str) -> None: self._theme = v
    theme = Property(str, _get_theme, _set_theme)

    def _get_font_family(self) -> str: return self._font_family
    def _set_font_family(self, v: str) -> None: self._font_family = v
    font_family = Property(str, _get_font_family, _set_font_family)

    def _get_font_size(self) -> int: return self._font_size
    def _set_font_size(self, v: int) -> None: self._font_size = max(10, min(48, v))
    font_size = Property(int, _get_font_size, _set_font_size)

    def _get_update_interval(self) -> int: return self._update_interval
    def _set_update_interval(self, v: int) -> None: self._update_interval = max(60, v)
    update_interval = Property(int, _get_update_interval, _set_update_interval)

    def _get_translation_api_url(self) -> str: return self._translation_api_url
    def _set_translation_api_url(self, v: str) -> None: self._translation_api_url = v
    translation_api_url = Property(str, _get_translation_api_url, _set_translation_api_url)

    def _get_translation_api_key(self) -> str: return self._translation_api_key
    def _set_translation_api_key(self, v: str) -> None: self._translation_api_key = v
    translation_api_key = Property(str, _get_translation_api_key, _set_translation_api_key)

    def _get_translation_model(self) -> str: return self._translation_model
    def _set_translation_model(self, v: str) -> None: self._translation_model = v
    translation_model = Property(str, _get_translation_model, _set_translation_model)
