"""Article List ViewModel – manages article list display, filtering, pagination."""

from PySide6.QtCore import QObject, Signal, Property

from ..services.article_service import ArticleService
from ..models.article import Article
from ..models.feed import Feed
from .base_viewmodel import BaseViewModel


class ArticleListViewModel(BaseViewModel):
    """ViewModel for the article list panel."""

    articles_changed = Signal()
    selection_changed = Signal(object)  # Article | None
    unread_count_changed = Signal(int)

    def __init__(
        self,
        article_service: ArticleService,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._article_service = article_service
        self._articles: list[Article] = []
        self._current_feed_id: int | None = None
        self._current_category_id: int | None = None
        self._filter_read: bool | None = None  # None=all, True=read, False=unread
        self._filter_favorited: bool = False
        self._search_keyword: str = ""
        self._sort_order: str = "published_at DESC"
        self._current_page: int = 0
        self._page_size: int = 50
        self._total_count: int = 0
        self._selected_article: Article | None = None

    # -- Properties --
    def _get_articles(self) -> list[Article]:
        return self._articles

    articles = Property(list, _get_articles, notify=articles_changed)

    def _get_selected_article(self):
        return self._selected_article

    selected_article = Property(object, _get_selected_article, notify=selection_changed)

    def _get_search_keyword(self) -> str:
        return self._search_keyword

    def _set_search_keyword(self, value: str) -> None:
        self._search_keyword = value

    search_keyword = Property(str, _get_search_keyword, _set_search_keyword)

    # -- Actions --
    def set_feed_filter(self, feed: Feed | None) -> None:
        self._current_feed_id = feed.id if feed else None
        self._current_category_id = None
        self._current_page = 0
        self.load_articles()

    def set_category_filter(self, category_id: int | None) -> None:
        self._current_category_id = category_id
        self._current_feed_id = None
        self._current_page = 0
        self.load_articles()

    def set_read_filter(self, show_unread_only: bool) -> None:
        self._filter_read = False if show_unread_only else None
        self._current_page = 0
        self.load_articles()

    def set_favorite_filter(self, show_favorites_only: bool) -> None:
        self._filter_favorited = show_favorites_only
        self._current_page = 0
        self.load_articles()

    def set_sort_order(self, order: str) -> None:
        self._sort_order = order
        self._current_page = 0
        self.load_articles()

    def search(self, keyword: str) -> None:
        self._search_keyword = keyword
        self._current_page = 0
        self.load_articles()

    def load_articles(self) -> None:
        """Load articles based on current filters."""
        self._set_busy(True)
        try:
            self._articles = self._article_service.get_articles(
                feed_id=self._current_feed_id,
                category_id=self._current_category_id,
                is_read=self._filter_read,
                is_favorited=True if self._filter_favorited else None,
                search_keyword=self._search_keyword,
                sort_order=self._sort_order,
                limit=self._page_size,
                offset=self._current_page * self._page_size,
            )
            self._total_count = self._article_service.get_article_count(
                feed_id=self._current_feed_id,
                category_id=self._current_category_id,
                is_read=self._filter_read,
                is_favorited=True if self._filter_favorited else None,
                search_keyword=self._search_keyword,
            )
            self.articles_changed.emit()
        finally:
            self._set_busy(False)

    def select_article(self, article: Article | None) -> None:
        self._selected_article = article
        if article and not article.is_read:
            self._article_service.mark_read(article.id)
            article.is_read = True
            self.articles_changed.emit()
        self.selection_changed.emit(article)

    def toggle_favorite(self, article: Article) -> None:
        new_state = self._article_service.toggle_favorite(article.id)
        article.is_favorited = new_state
        self.articles_changed.emit()

    def mark_all_read(self) -> None:
        feed_id = self._current_feed_id
        self._article_service.mark_all_read(feed_id)
        self.load_articles()

    def next_page(self) -> bool:
        if (self._current_page + 1) * self._page_size < self._total_count:
            self._current_page += 1
            self.load_articles()
            return True
        return False

    def prev_page(self) -> bool:
        if self._current_page > 0:
            self._current_page -= 1
            self.load_articles()
            return True
        return False

    def load_unread_count(self) -> None:
        count = self._article_service.get_total_unread_count()
        self.unread_count_changed.emit(count)
