"""Full Article Translation Dialog – translates entire article content with progress bar and clean text."""

import html as html_mod

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QLabel, QTextBrowser, QSplitter, QProgressBar, QWidget,
)

from ..viewmodels.full_translation_viewmodel import FullTranslationViewModel


class FullTranslationDialog(QDialog):
    """Dialog for translating full article content with progress and parallel comparison."""

    def __init__(self, viewmodel: FullTranslationViewModel, parent=None):
        super().__init__(parent)
        self._vm = viewmodel
        self.setWindowTitle("全文翻译")
        self.resize(900, 700)
        self.setMinimumSize(600, 450)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ── Top bar: language selection + translate button ──
        top_bar = QHBoxLayout()

        top_bar.addWidget(QLabel("原文语言:"))
        self._src_lang = QComboBox()
        self._src_lang.addItems(["英文", "中文", "自动检测"])
        self._src_lang.setCurrentIndex(2)
        top_bar.addWidget(self._src_lang)

        self._swap_label = QLabel(" → ")
        self._swap_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        top_bar.addWidget(self._swap_label)

        top_bar.addWidget(QLabel("目标语言:"))
        self._tgt_lang = QComboBox()
        self._tgt_lang.addItems(["中文", "英文"])
        self._tgt_lang.setCurrentIndex(0)
        top_bar.addWidget(self._tgt_lang)

        top_bar.addStretch()

        self._translate_btn = QPushButton("翻译全文")
        self._translate_btn.setStyleSheet(
            "font-weight: bold; padding: 6px 20px; background: #1a73e8; color: white; "
            "border: none; border-radius: 6px;"
        )
        self._translate_btn.clicked.connect(self._on_translate)
        top_bar.addWidget(self._translate_btn)

        layout.addLayout(top_bar)

        # ── Progress bar with status label ──
        progress_row = QHBoxLayout()
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setMinimum(0)
        self._progress.setMaximum(100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setMaximumHeight(6)
        progress_row.addWidget(self._progress, 1)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #666; font-size: 11px;")
        self._status_label.setVisible(False)
        progress_row.addWidget(self._status_label)

        layout.addLayout(progress_row)

        # ── Split panel: original top, translated bottom ──
        splitter = QSplitter(Qt.Vertical)

        # Original content
        orig_widget = QWidget()
        orig_layout = QVBoxLayout(orig_widget)
        orig_layout.setContentsMargins(0, 0, 0, 0)
        orig_layout.setSpacing(4)

        orig_header = QLabel(
            f"原文 ({'?'} 字)"
        )
        orig_header.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #1a73e8; "
            "padding: 4px 0; border-bottom: 2px solid #1a73e8;"
        )
        self._orig_header = orig_header
        orig_layout.addWidget(self._orig_header)

        self._orig_browser = QTextBrowser()
        self._orig_browser.setOpenExternalLinks(True)
        orig_layout.addWidget(self._orig_browser)

        splitter.addWidget(orig_widget)

        # Translated content
        tgt_widget = QWidget()
        tgt_layout = QVBoxLayout(tgt_widget)
        tgt_layout.setContentsMargins(0, 0, 0, 0)
        tgt_layout.setSpacing(4)

        tgt_header = QLabel("译文")
        tgt_header.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #34a853; "
            "padding: 4px 0; border-bottom: 2px solid #34a853;"
        )
        tgt_layout.addWidget(tgt_header)

        self._tgt_browser = QTextBrowser()
        self._tgt_browser.setOpenExternalLinks(True)
        tgt_layout.addWidget(self._tgt_browser)

        splitter.addWidget(tgt_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        # ── Close button ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        # ── VM bindings ──
        self._vm.translation_ready.connect(self._on_result)
        self._vm.busy_changed.connect(self._on_busy)
        self._vm.progress_changed.connect(self._on_progress)

        # Load initial content
        self._display_original()

    def _display_original(self) -> None:
        """Display the original (HTML-stripped) article content."""
        title = self._vm.original_title
        content = self._vm.original_content
        word_count = self._vm.original_word_count

        self._orig_header.setText(f"原文（{word_count} 词/字）")

        html_parts = [
            '<div style="font-family: Microsoft YaHei, sans-serif; line-height: 1.8; '
            'padding: 4px;">',
        ]

        if title:
            html_parts.append(
                f'<h2 style="font-size: 20px; margin-bottom: 12px; color: #1a1a1a;">'
                f'{html_mod.escape(title)}</h2>'
            )

        if content:
            paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
            for p in paragraphs:
                html_parts.append(f"<p>{html_mod.escape(p)}</p>")
        else:
            html_parts.append("<p style='color: #999;'>(无内容)</p>")

        html_parts.append("</div>")
        self._orig_browser.setHtml("".join(html_parts))

    def _on_translate(self) -> None:
        """Start full article translation."""
        lang_map = {"英文": "en", "中文": "zh", "自动检测": "auto"}
        tgt_map = {"中文": "zh", "英文": "en"}

        self._vm._source_lang = lang_map[self._src_lang.currentText()]
        self._vm._target_lang = tgt_map[self._tgt_lang.currentText()]
        self._vm.translate_full()

    def _on_progress(self, percent: int, status: str) -> None:
        """Update progress bar and status text."""
        self._progress.setValue(percent)
        self._status_label.setText(status)
        self._tgt_browser.setHtml(
            f'<div style="color: #888; padding: 20px; text-align: center; '
            f'font-family: Microsoft YaHei;">'
            f'<p style="font-size: 14px;">{status}</p>'
            f'<p style="font-size: 12px;">{percent}%</p></div>'
        )

    def _on_result(self) -> None:
        """Display the translated content."""
        translated_content = self._vm.translated_content

        if translated_content.startswith("[") and "]" in translated_content:
            self._tgt_browser.setHtml(
                f'<div style="color: #d93025; padding: 12px; '
                f'font-family: Microsoft YaHei;">'
                f'{html_mod.escape(translated_content)}</div>'
            )
            return

        # Build paragraph-aligned comparison
        src_paragraphs = [p.strip() for p in self._vm.original_content.split("\n") if p.strip()]
        tgt_paragraphs = [p.strip() for p in translated_content.split("\n") if p.strip()]

        src_label = self._src_lang.currentText()
        tgt_label = self._tgt_lang.currentText()
        translated_title = self._vm.translated_title

        html_parts = [
            '<div style="font-family: Microsoft YaHei, sans-serif; line-height: 1.8;">',
        ]

        if translated_title:
            html_parts.append(
                f'<h2 style="font-size: 20px; margin-bottom: 12px; color: #34a853;">'
                f'{html_mod.escape(translated_title)}</h2>'
            )

        max_paras = max(len(src_paragraphs), len(tgt_paragraphs))
        for i in range(max_paras):
            src_p = src_paragraphs[i] if i < len(src_paragraphs) else ""
            tgt_p = tgt_paragraphs[i] if i < len(tgt_paragraphs) else ""

            if src_p:
                html_parts.append(
                    f'<div style="background:#f0f4ff; padding:8px 10px; margin:4px 0; '
                    f'border-left:3px solid #1a73e8; border-radius:3px;">'
                    f'<span style="font-size:11px; color:#1a73e8; font-weight:bold;">'
                    f'原文 ({src_label})</span><br>{html_mod.escape(src_p)}</div>'
                )
            if tgt_p:
                html_parts.append(
                    f'<div style="background:#f6fff6; padding:8px 10px; margin:4px 0; '
                    f'border-left:3px solid #34a853; border-radius:3px;">'
                    f'<span style="font-size:11px; color:#34a853; font-weight:bold;">'
                    f'译文 ({tgt_label})</span><br>{html_mod.escape(tgt_p)}</div>'
                )
            if src_p and tgt_p and i < max_paras - 1:
                html_parts.append(
                    '<hr style="border:none;border-top:1px dashed #ddd;margin:6px 0;">'
                )

        html_parts.append("</div>")
        self._tgt_browser.setHtml("".join(html_parts))

    def _on_busy(self, busy: bool) -> None:
        self._translate_btn.setEnabled(not busy)
        self._translate_btn.setText("翻译中..." if busy else "翻译全文")
        self._progress.setVisible(busy)
        self._status_label.setVisible(busy)
        if not busy:
            self._progress.setValue(100)
            self._status_label.setText("翻译完成")
