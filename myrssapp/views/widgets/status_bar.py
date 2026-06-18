"""Custom status bar widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class StatusWidget(QWidget):
    """Status bar widget showing unread count and sync status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)

        self._unread_label = QLabel("未读: 0")
        self._unread_label.setStyleSheet("color: #1a73e8; font-weight: bold;")
        layout.addWidget(self._unread_label)

        layout.addStretch()

        self._sync_label = QLabel("就绪")
        self._sync_label.setStyleSheet("color: #888;")
        layout.addWidget(self._sync_label)

    def set_unread_count(self, count: int) -> None:
        self._unread_label.setText(f"未读: {count}")

    def set_sync_status(self, status: str) -> None:
        self._sync_label.setText(status)
