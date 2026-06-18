"""Translation panel widget – displays parallel comparison (原文+译文对照)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QComboBox, QLabel, QTextBrowser,
)

from ..viewmodels.translation_viewmodel import TranslationViewModel


class TranslationPanel(QWidget):
    """Side panel for AI-powered Chinese-English translation with parallel comparison."""

    def __init__(self, viewmodel: TranslationViewModel, parent=None):
        super().__init__(parent)
        self._vm = viewmodel
        self.setMinimumWidth(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("AI 翻译")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Language selector
        lang_layout = QHBoxLayout()
        self._source_lang = QComboBox()
        self._source_lang.addItem("英文", "en")
        self._source_lang.addItem("中文", "zh")
        self._source_lang.addItem("自动检测", "auto")
        self._source_lang.setCurrentIndex(0)
        lang_layout.addWidget(self._source_lang)

        swap_btn = QPushButton("⇄")
        swap_btn.setMaximumWidth(40)
        swap_btn.clicked.connect(self._on_swap)
        lang_layout.addWidget(swap_btn)

        self._target_lang = QComboBox()
        self._target_lang.addItem("中文", "zh")
        self._target_lang.addItem("英文", "en")
        self._target_lang.setCurrentIndex(0)
        lang_layout.addWidget(self._target_lang)

        layout.addLayout(lang_layout)

        # Source text input
        src_label = QLabel("原文")
        src_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(src_label)
        self._source_edit = QTextEdit()
        self._source_edit.setPlaceholderText("输入要翻译的文本...")
        self._source_edit.setMaximumHeight(120)
        layout.addWidget(self._source_edit)

        # Translate button
        self._translate_btn = QPushButton("翻译")
        self._translate_btn.setStyleSheet("font-weight: bold; height: 32px;")
        self._translate_btn.clicked.connect(self._on_translate)
        layout.addWidget(self._translate_btn)

        # Comparison output: QTextBrowser supports HTML formatting
        tgt_label = QLabel("对照结果")
        tgt_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(tgt_label)
        self._output_browser = QTextBrowser()
        self._output_browser.setOpenExternalLinks(True)
        self._output_browser.setPlaceholderText("翻译结果将以原文/译文对照显示...")
        layout.addWidget(self._output_browser)

        # VM bindings
        self._vm.translation_ready.connect(self._on_translation_ready)
        self._vm.busy_changed.connect(self._on_busy_changed)

    def set_source_text(self, text: str) -> None:
        self._source_edit.setPlainText(text)

    def _on_translate(self) -> None:
        self._vm.source_text = self._source_edit.toPlainText()
        self._vm.source_lang = self._source_lang.currentData()
        self._vm.target_lang = self._target_lang.currentData()
        self._vm.translate()

    def _on_translation_ready(self) -> None:
        self._output_browser.setHtml(self._vm.target_text)

    def _on_busy_changed(self, busy: bool) -> None:
        self._translate_btn.setEnabled(not busy)
        self._translate_btn.setText("翻译中..." if busy else "翻译")

    def _on_swap(self) -> None:
        self._vm.swap_languages()
        # 交换后同步下拉框
        idx = self._source_lang.findData(self._vm.source_lang)
        if idx >= 0:
            self._source_lang.setCurrentIndex(idx)
        idx = self._target_lang.findData(self._vm.target_lang)
        if idx >= 0:
            self._target_lang.setCurrentIndex(idx)
