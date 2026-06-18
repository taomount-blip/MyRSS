"""Feed List ViewModel – manages the subscription tree."""

from PySide6.QtCore import QObject, Signal, Property

from ..services.feed_service import FeedService
from ..models.feed import Feed
from ..models.category import Category
from .base_viewmodel import BaseViewModel


class FeedListViewModel(BaseViewModel):
    """ViewModel for the feed subscription sidebar."""

    feeds_changed = Signal()
    categories_changed = Signal()
    selected_feed_changed = Signal(object)  # Feed | Category | None

    def __init__(
        self,
        feed_service: FeedService,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._feed_service = feed_service
        self._feeds: list[Feed] = []
        self._categories: list[Category] = []
        self._selected_feed: Feed | None = None
        self._selected_category: Category | None = None
        self._show_all = True  # "全部文章" node

    # -- Properties --
    def _get_feeds(self) -> list[Feed]:
        return self._feeds

    feeds = Property(list, _get_feeds, notify=feeds_changed)

    def _get_categories(self) -> list[Category]:
        return self._categories

    categories = Property(list, _get_categories, notify=categories_changed)

    def _get_selected_feed(self):
        return self._selected_feed

    selected_feed = Property(object, _get_selected_feed, notify=selected_feed_changed)

    # -- Actions --
    def load_feeds(self) -> None:
        """Reload all feeds and categories from the database."""
        self._feeds = self._feed_service.get_all_feeds()
        self._categories = self._feed_service.get_all_categories()
        self.feeds_changed.emit()
        self.categories_changed.emit()

    def select_feed(self, feed: Feed | None) -> None:
        self._selected_feed = feed
        self.selected_feed_changed.emit(feed)

    def select_category(self, category: Category | None) -> None:
        self._selected_category = category
        self.selected_feed_changed.emit(None)  # triggers category filter in article list

    def delete_feed(self, feed_id: int) -> None:
        from ..services.article_service import ArticleService
        ArticleService(self._feed_service._db)  # Just to trigger CASCADE deletion
        self._feed_service.delete_feed(feed_id)
        self.load_feeds()
        if self._selected_feed and self._selected_feed.id == feed_id:
            self._selected_feed = None
            self.selected_feed_changed.emit(None)

    def refresh_feed(self, feed_id: int) -> None:
        """Refresh a single feed."""
        from ..services.fetch_service import FetchService
        fetcher = FetchService(self._feed_service._db)
        feed = self._feed_service.get_feed(feed_id)
        if feed:
            self._set_busy(True)
            try:
                fetcher.fetch_feed(feed)
            finally:
                self._set_busy(False)
            self.load_feeds()

    def get_feeds_for_category(self, category_id: int) -> list[Feed]:
        return [f for f in self._feeds if f.category_id == category_id]

    def get_uncategorized_feeds(self) -> list[Feed]:
        return [f for f in self._feeds if f.category_id is None]
