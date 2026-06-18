"""Translation ViewModel – supports parallel comparison output."""

import html as html_mod

from PySide6.QtCore import QObject, Signal, Property

from ..services.translation_service import TranslationService
from .base_viewmodel import BaseViewModel


LANG_LABELS = {
    "en": "English",
    "zh": "中文",
    "auto": "自动检测",
}


class TranslationViewModel(BaseViewModel):
    """ViewModel for the translation panel."""

    translation_ready = Signal()

    def __init__(
        self,
        translation_service: TranslationService,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._translation_service = translation_service
        self._source_text: str = ""
        self._target_text: str = ""
        self._source_lang: str = "en"
        self._target_lang: str = "zh"
        # 对照模式: True=对照显示, False=只显示译文
        self._comparison_mode: bool = True

    def _get_source_text(self) -> str: return self._source_text
    def _set_source_text(self, v: str) -> None: self._source_text = v
    source_text = Property(str, _get_source_text, _set_source_text)

    def _get_target_text(self) -> str:
        return self._target_text

    target_text = Property(str, _get_target_text, notify=translation_ready)

    def _get_source_lang(self) -> str: return self._source_lang
    def _set_source_lang(self, v: str) -> None: self._source_lang = v
    source_lang = Property(str, _get_source_lang, _set_source_lang)

    def _get_target_lang(self) -> str: return self._target_lang
    def _set_target_lang(self, v: str) -> None: self._target_lang = v
    target_lang = Property(str, _get_target_lang, _set_target_lang)

    def translate(self) -> None:
        if not self._source_text.strip():
            self._emit_error("请输入要翻译的文本")
            return
        self._set_busy(True)
        try:
            raw_result = self._translation_service.translate(
                self._source_text.strip(),
                source_lang=self._source_lang,
                target_lang=self._target_lang,
            )
            if raw_result is None:
                self._target_text = "翻译失败，请检查 API 配置"
            elif raw_result.startswith("[") and "]" in raw_result:
                # 错误消息透传
                self._target_text = raw_result
            else:
                self._build_comparison_output(raw_result)
        except Exception as e:
            self._target_text = str(e)
        finally:
            self._set_busy(False)
            self.translation_ready.emit()

    def _build_comparison_output(self, translated: str) -> None:
        """Build HTML with parallel comparison of source and translation."""
        src = self._source_text.strip()
        src_label = LANG_LABELS.get(self._source_lang, self._source_lang)
        tgt_label = LANG_LABELS.get(self._target_lang, self._target_lang)

        # Split into paragraphs for alignment
        src_paragraphs = [p.strip() for p in src.split("\n") if p.strip()]
        tgt_paragraphs = [p.strip() for p in translated.split("\n") if p.strip()]

        if self._comparison_mode:
            html_parts = [
                '<div style="font-family: Microsoft YaHei, sans-serif; font-size: 13px; line-height: 1.7;">',
                f'<h3 style="margin: 0 0 8px 0; color: #333; font-size: 14px;">对照翻译</h3>',
            ]

            # Show paragraph-by-paragraph comparison
            max_paragraphs = max(len(src_paragraphs), len(tgt_paragraphs))
            for i in range(max_paragraphs):
                src_p = src_paragraphs[i] if i < len(src_paragraphs) else ""
                tgt_p = tgt_paragraphs[i] if i < len(tgt_paragraphs) else ""

                if src_p:
                    html_parts.append(
                        f'<div style="background:#f0f4ff; padding:8px 10px; '
                        f'margin:4px 0; border-left:3px solid #1a73e8; '
                        f'border-radius:3px;">'
                        f'<span style="font-size:11px; color:#1a73e8; font-weight:bold;">'
                        f'原文 ({src_label})</span><br>'
                        f'{html_mod.escape(src_p)}</div>'
                    )
                if tgt_p:
                    html_parts.append(
                        f'<div style="background:#f6fff6; padding:8px 10px; '
                        f'margin:4px 0; border-left:3px solid #34a853; '
                        f'border-radius:3px;">'
                        f'<span style="font-size:11px; color:#34a853; font-weight:bold;">'
                        f'译文 ({tgt_label})</span><br>'
                        f'{html_mod.escape(tgt_p)}</div>'
                    )

                if src_p and tgt_p and i < max_paragraphs - 1:
                    html_parts.append(
                        '<hr style="border:none;border-top:1px dashed #ddd;margin:4px 0;">'
                    )

            html_parts.append("</div>")
            self._target_text = "".join(html_parts)
        else:
            # Simple mode: just translated text
            self._target_text = translated

    def swap_languages(self) -> None:
        self._source_lang, self._target_lang = self._target_lang, self._source_lang
        self._source_text, self._target_text = self._target_text, self._source_text
        self.translation_ready.emit()

    def clear(self) -> None:
        self._source_text = ""
        self._target_text = ""
