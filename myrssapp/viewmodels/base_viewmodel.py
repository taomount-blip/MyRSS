"""Base ViewModel class – QObject with Signal/Property support."""

from PySide6.QtCore import QObject, Signal


class BaseViewModel(QObject):
    """Foundation for all ViewModels. Provides service injection and error signalling."""

    error_occurred = Signal(str)
    busy_changed = Signal(bool)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._is_busy = False

    @property
    def is_busy(self) -> bool:
        return self._is_busy

    def _set_busy(self, busy: bool) -> None:
        if self._is_busy != busy:
            self._is_busy = busy
            self.busy_changed.emit(busy)

    def _emit_error(self, message: str) -> None:
        self.error_occurred.emit(message)
