"""Search bar widget with filter dropdown."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
)


class SearchBar(QWidget):
    """Search bar with integrated filter controls."""

    search_requested = Signal(str)
    cleared = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self._input = QLineEdit()
        self._input.setPlaceholderText("搜索文章...")
        self._input.setClearButtonEnabled(True)
        self._input.returnPressed.connect(self._on_search)
        layout.addWidget(self._input)

        search_btn = QPushButton("搜索")
        search_btn.setMaximumWidth(60)
        search_btn.clicked.connect(self._on_search)
        layout.addWidget(search_btn)

    def _on_search(self) -> None:
        text = self._input.text().strip()
        if text:
            self.search_requested.emit(text)
        else:
            self.cleared.emit()

    def clear(self) -> None:
        self._input.clear()
        self.cleared.emit()
