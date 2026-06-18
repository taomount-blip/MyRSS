"""Add Feed dialog."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QFormLayout, QTextEdit, QProgressBar,
)

from ..viewmodels.add_feed_viewmodel import AddFeedViewModel


class AddFeedDialog(QDialog):
    """Dialog for adding a new RSS feed subscription."""

    def __init__(self, viewmodel: AddFeedViewModel, parent=None):
        super().__init__(parent)
        self._vm = viewmodel
        self.setWindowTitle("添加订阅")
        self.setMinimumWidth(450)
        self.resize(480, 300)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()

        # URL input
        url_layout = QHBoxLayout()
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("https://example.com/rss")
        url_layout.addWidget(self._url_input)

        self._preview_btn = QPushButton("预览")
        self._preview_btn.setMaximumWidth(60)
        self._preview_btn.clicked.connect(self._on_preview)
        url_layout.addWidget(self._preview_btn)
        form.addRow("RSS 地址:", url_layout)

        # Category selector
        self._category_combo = QComboBox()
        self._category_combo.addItem("(无分类)", None)
        form.addRow("分类:", self._category_combo)

        layout.addLayout(form)

        # Preview area
        self._preview_area = QTextEdit()
        self._preview_area.setReadOnly(True)
        self._preview_area.setMaximumHeight(100)
        self._preview_area.setPlaceholderText("点击「预览」查看订阅源信息")
        layout.addWidget(self._preview_area)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        layout.addWidget(self._progress)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._add_btn = QPushButton("添加")
        self._add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self._add_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # VM bindings
        self._vm.feed_preview_ready.connect(self._on_preview_ready)
        self._vm.busy_changed.connect(self._on_busy_changed)
        self._vm.error_occurred.connect(self._on_error)
        self._vm.feed_added.connect(self.accept)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # Load categories
        self._vm.load_categories()
        self._category_combo.clear()
        self._category_combo.addItem("(无分类)", None)
        for cat in self._vm._categories:
            self._category_combo.addItem(cat.name, cat.id)

    def _on_preview(self) -> None:
        self._vm.feed_url = self._url_input.text()
        self._vm.preview_feed()

    def _on_preview_ready(self, title: str, description: str) -> None:
        self._preview_area.setPlainText(f"标题: {title}\n{description}")

    def _on_add(self) -> None:
        self._vm.feed_url = self._url_input.text()
        self._vm._selected_category_id = self._category_combo.currentData()
        self._vm.confirm_add()

    def _on_busy_changed(self, busy: bool) -> None:
        self._progress.setVisible(busy)
        if busy:
            self._progress.setRange(0, 0)
        self._add_btn.setEnabled(not busy)
        self._preview_btn.setEnabled(not busy)

    def _on_error(self, message: str) -> None:
        self._preview_area.setPlainText(f"错误: {message}")
