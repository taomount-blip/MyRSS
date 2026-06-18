"""Article detail view – QWebEngineView with translation toolbar."""

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from ..viewmodels.article_detail_viewmodel import ArticleDetailViewModel


class ArticleDetailView(QWidget):
    """Article reading panel: toolbar + QWebEngineView for HTML rendering."""

    translate_full_requested = Signal(object)  # emits Article

    def __init__(self, viewmodel: ArticleDetailViewModel, parent=None):
        super().__init__(parent)
        self._vm = viewmodel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 4, 8, 4)
        toolbar.setSpacing(8)

        self._title_label = QLabel("选择一个文章开始阅读")
        self._title_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #333;"
        )
        toolbar.addWidget(self._title_label, 1)

        self._translate_btn = QPushButton("全文翻译")
        self._translate_btn.setStyleSheet(
            "padding: 4px 14px; font-size: 12px; background: #1a73e8; color: white; "
            "border: none; border-radius: 4px;"
        )
        self._translate_btn.clicked.connect(self._on_translate_full)
        self._translate_btn.setVisible(False)
        toolbar.addWidget(self._translate_btn)

        layout.addLayout(toolbar)

        # WebEngine for article content
        self._webview = QWebEngineView()
        self._webview.setHtml("<html><body></body></html>")
        layout.addWidget(self._webview, 1)

        # VM bindings
        self._vm.article_changed.connect(self._on_article_changed)

    def _on_article_changed(self) -> None:
        article = self._vm.article
        if article:
            html = self._vm.html
            if html:
                self._webview.setHtml(html)
            self._title_label.setText(article.title or "(无标题)")
            self._translate_btn.setVisible(True)
        else:
            self._webview.setHtml(self._empty_page())
            self._title_label.setText("选择一个文章开始阅读")
            self._translate_btn.setVisible(False)

    def _on_translate_full(self) -> None:
        article = self._vm.article
        if article:
            self.translate_full_requested.emit(article)

    @staticmethod
    def _empty_page() -> str:
        return """<!DOCTYPE html>
<html><body style="
    display:flex;align-items:center;justify-content:center;
    height:100vh;margin:0;font-family:'Microsoft YaHei',sans-serif;
    color:#888;font-size:16px;user-select:none;">
    <div>选择一个文章开始阅读</div>
</body></html>"""
