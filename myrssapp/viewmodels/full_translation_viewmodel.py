"""Full Article Translation ViewModel – strips HTML, reports progress."""

from bs4 import BeautifulSoup

from PySide6.QtCore import QObject, Signal, Property

from ..services.translation_service import TranslationService
from ..models.article import Article
from .base_viewmodel import BaseViewModel


class FullTranslationViewModel(BaseViewModel):
    """ViewModel for translating the full article content."""

    translation_ready = Signal()
    progress_changed = Signal(int, str)  # (percent, status_text)

    def __init__(
        self,
        translation_service: TranslationService,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._translation_service = translation_service
        self._source_lang: str = "en"
        self._target_lang: str = "zh"
        self._original_title: str = ""
        self._original_content_raw: str = ""      # HTML stripped, for clean display
        self._original_content_plain: str = ""     # pure text for translation
        self._translated_title: str = ""
        self._translated_content: str = ""

    # ------------------------------------------------------------------
    # Plain-text content helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _strip_html(html_content: str) -> str:
        """Strip HTML tags, returning clean plain text."""
        if not html_content:
            return ""
        try:
            soup = BeautifulSoup(html_content, "lxml")
            # Remove script and style blocks
            for tag in soup(["script", "style", "iframe"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
            # Collapse multiple blank lines
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return "\n".join(lines)
        except Exception:
            # Fallback: simple tag stripping
            import re
            text = re.sub(r"<[^>]+>", "", html_content)
            return "\n".join(
                line.strip() for line in text.split("\n") if line.strip()
            )

    def load_article(self, article: Article) -> None:
        self._original_title = article.title or ""
        raw_html = article.content or article.summary or ""
        self._original_content_raw = self._strip_html(raw_html)
        self._original_content_plain = self._original_content_raw  # already plain text

    @property
    def original_title(self) -> str:
        return self._original_title

    @property
    def original_content(self) -> str:
        """Clean text for display (HTML stripped)."""
        return self._original_content_raw

    @property
    def translated_title(self) -> str:
        return self._translated_title

    @property
    def translated_content(self) -> str:
        return self._translated_content

    @property
    def original_word_count(self) -> int:
        """Approximate word count of the original content."""
        return len(self._original_content_plain.split())

    # ------------------------------------------------------------------
    # Translation (with progress)
    # ------------------------------------------------------------------
    def translate_full(self) -> None:
        """Translate title and content sequentially with progress updates."""
        if not self._original_content_plain.strip():
            self._emit_error("文章内容为空，无法翻译")
            return

        self._set_busy(True)
        self.progress_changed.emit(0, "准备翻译...")

        try:
            total_char = len(self._original_content_plain)
            est_tokens = max(1, total_char // 2)

            # ── Step 1: Translate title ──
            if self._original_title.strip():
                self.progress_changed.emit(5, "正在翻译标题...")
                title_result = self._translation_service.translate(
                    self._original_title.strip(),
                    source_lang=self._source_lang,
                    target_lang=self._target_lang,
                )
                if title_result and not title_result.startswith("["):
                    self._translated_title = title_result
                else:
                    self._translated_title = self._original_title
            else:
                self._translated_title = ""

            # ── Step 2: Estimate chunks for large content ──
            self.progress_changed.emit(15, "正在翻译正文 (0%)...")

            content = self._original_content_plain.strip()
            if est_tokens > 3000:
                # Chunk large content into segments
                chunks = self._split_into_chunks(content, max_chars=4000)
                translated_parts = []
                total_chunks = len(chunks)

                for idx, chunk in enumerate(chunks):
                    pct = 15 + int((idx + 1) / total_chunks * 80)
                    self.progress_changed.emit(
                        pct, f"正在翻译正文 ({int((idx+1)/total_chunks*100)}%)..."
                    )

                    chunk_result = self._translation_service.translate(
                        chunk, source_lang=self._source_lang,
                        target_lang=self._target_lang,
                    )
                    if chunk_result and not chunk_result.startswith("["):
                        translated_parts.append(chunk_result)
                    else:
                        translated_parts.append(chunk)

                full_translated = "\n\n".join(translated_parts)
            else:
                # Short enough for single pass
                self.progress_changed.emit(30, "正在翻译全文...")
                content_result = self._translation_service.translate(
                    content, source_lang=self._source_lang,
                    target_lang=self._target_lang,
                )
                full_translated = content_result if (content_result and not content_result.startswith("[")) else (content_result or "翻译失败")

            self._translated_content = full_translated
            self.progress_changed.emit(100, "翻译完成")
            self.translation_ready.emit()

        except Exception as e:
            self._translated_content = f"[错误] {e}"
            self.progress_changed.emit(100, "翻译出错")
            self.translation_ready.emit()
        finally:
            self._set_busy(False)

    # ------------------------------------------------------------------
    # Chunking for long articles
    # ------------------------------------------------------------------
    @staticmethod
    def _split_into_chunks(text: str, max_chars: int) -> list[str]:
        """Split long text into paragraph-aligned chunks."""
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        chunks: list[str] = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) + 1 > max_chars and current:
                chunks.append(current)
                current = para
            else:
                current = (current + "\n" + para).strip()
        if current:
            chunks.append(current)

        return chunks if chunks else [text]

    def clear(self) -> None:
        self._original_title = ""
        self._original_content_raw = ""
        self._original_content_plain = ""
        self._translated_title = ""
        self._translated_content = ""
