"""Article Detail ViewModel – displays article content."""

from PySide6.QtCore import QObject, Signal, Property

from ..services.article_service import ArticleService
from ..models.article import Article
from .base_viewmodel import BaseViewModel


class ArticleDetailViewModel(BaseViewModel):
    """ViewModel for the article reading panel."""

    article_changed = Signal()

    def __init__(
        self,
        article_service: ArticleService,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._article_service = article_service
        self._article: Article | None = None
        self._html: str = ""

    # -- Properties --
    def _get_article(self):
        return self._article

    article = Property(object, _get_article, notify=article_changed)

    def _get_html(self) -> str:
        return self._html

    html = Property(str, _get_html, notify=article_changed)

    # -- Actions --
    def load_article(self, article_id: int) -> None:
        self._article = self._article_service.get_article(article_id)
        if self._article:
            self._build_html()
        else:
            self._html = ""
        self.article_changed.emit()

    def load_article_obj(self, article: Article) -> None:
        self._article = article
        self._build_html()
        self.article_changed.emit()

    def clear(self) -> None:
        self._article = None
        self._html = ""
        self.article_changed.emit()

    def _build_html(self) -> None:
        """Create a styled HTML page with the article content."""
        article = self._article
        if not article:
            self._html = ""
            return

        title = article.title or "(无标题)"
        author = article.author or ""
        feed_title = article.feed_title or ""
        link = article.link or ""
        published = article.published_at or ""
        content = article.content or article.summary or ""

        # Strip out dangerous tags / scripts
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(["script", "iframe", "object", "embed"]):
            tag.decompose()
        safe_content = str(soup)

        self._html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 16px;
    line-height: 1.8;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    word-wrap: break-word;
  }}
  h1.title {{
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 8px;
    color: #1a1a1a;
  }}
  .meta {{
    color: #888;
    font-size: 13px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e0e0e0;
  }}
  .meta span {{
    margin-right: 16px;
  }}
  .content img {{
    max-width: 100%;
    height: auto;
  }}
  .content a {{
    color: #1a73e8;
  }}
  .content pre {{
    background: #f5f5f5;
    padding: 12px;
    border-radius: 4px;
    overflow-x: auto;
    white-space: pre-wrap;
  }}
  .content blockquote {{
    border-left: 4px solid #1a73e8;
    margin: 16px 0;
    padding: 4px 16px;
    color: #555;
    background: #f9f9f9;
  }}
  .open-link {{
    display: inline-block;
    margin-top: 24px;
    padding: 8px 16px;
    background: #1a73e8;
    color: white;
    text-decoration: none;
    border-radius: 6px;
    font-size: 14px;
  }}
</style>
</head>
<body>
<h1 class="title">{title}</h1>
<div class="meta">
  <span>来源: {feed_title}</span>
  {f'<span>作者: {author}</span>' if author else ''}
  {f'<span>时间: {published}</span>' if published else ''}
</div>
<div class="content">{safe_content}</div>
{f'<a class="open-link" href="{link}">在浏览器中打开</a>' if link else ''}
</body>
</html>"""
