"""Main ViewModel – top-level coordinator for all sub-ViewModels."""

from PySide6.QtCore import QObject, Property, QTimer, Signal

from ..services.feed_service import FeedService
from ..services.article_service import ArticleService
from ..services.fetch_service import FetchService
from ..services.translation_service import TranslationService
from ..services.settings_service import SettingsService
from ..models.feed import Feed
from ..models.article import Article
from .base_viewmodel import BaseViewModel
from .feed_list_viewmodel import FeedListViewModel
from .article_list_viewmodel import ArticleListViewModel
from .article_detail_viewmodel import ArticleDetailViewModel
from .add_feed_viewmodel import AddFeedViewModel
from .settings_viewmodel import SettingsViewModel
from .translation_viewmodel import TranslationViewModel


class MainViewModel(BaseViewModel):
    """Top-level ViewModel that wires together all child ViewModels."""

    sync_status_changed = Signal(str)

    def __init__(
        self,
        feed_service: FeedService,
        article_service: ArticleService,
        fetch_service: FetchService,
        translation_service: TranslationService,
        settings_service: SettingsService,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._feed_service = feed_service
        self._article_service = article_service
        self._fetch_service = fetch_service
        self._settings_service = settings_service
        self._translation_service = translation_service

        # Child ViewModels
        self.feed_list_vm = FeedListViewModel(feed_service, self)
        self.article_list_vm = ArticleListViewModel(article_service, self)
        self.article_detail_vm = ArticleDetailViewModel(article_service, self)
        self.add_feed_vm = AddFeedViewModel(feed_service, fetch_service, self)
        self.settings_vm = SettingsViewModel(settings_service, self)
        self.translation_vm = TranslationViewModel(translation_service, self)

        self._sync_status = "就绪"
        self._unread_count = 0

        # Wire signals
        self.feed_list_vm.selected_feed_changed.connect(self._on_feed_selected)
        self.article_list_vm.selection_changed.connect(self._on_article_selected)
        self.add_feed_vm.feed_added.connect(self._on_feed_added)

        # Auto-refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._schedule_auto_refresh()

        # Initial load
        self.feed_list_vm.load_feeds()
        self.article_list_vm.load_unread_count()
        self.article_list_vm.unread_count_changed.connect(
            lambda c: setattr(self, '_unread_count', c)
        )

    # -- Properties --
    def _get_sync_status(self) -> str:
        return self._sync_status

    sync_status = Property(str, _get_sync_status, notify=sync_status_changed)

    # -- Signal handlers --
    def _on_feed_selected(self, feed: Feed | None) -> None:
        if feed:
            self.article_list_vm.set_feed_filter(feed)
        else:
            self.article_list_vm.set_feed_filter(None)
            self.article_list_vm.load_articles()

    def _on_article_selected(self, article: Article | None) -> None:
        if article:
            self.article_detail_vm.load_article_obj(article)
        else:
            self.article_detail_vm.clear()

    def _on_feed_added(self, feed: Feed) -> None:
        self.feed_list_vm.load_feeds()
        self.article_list_vm.load_articles()
        self.article_list_vm.load_unread_count()

    # -- Actions --
    def refresh_all(self) -> None:
        """Manually refresh all feeds."""
        self._sync_status = "正在刷新..."
        self.sync_status_changed.emit(self._sync_status)
        self._set_busy(True)
        try:
            results = self._fetch_service.fetch_all_active()
            total_new = sum(results.values())
            self._sync_status = f"刷新完成，获取 {total_new} 篇新文章"
        except Exception as e:
            self._sync_status = f"刷新失败: {e}"
        finally:
            self._set_busy(False)
            self.sync_status_changed.emit(self._sync_status)
            self.feed_list_vm.load_feeds()
            self.article_list_vm.load_articles()
            self.article_list_vm.load_unread_count()

    def _auto_refresh(self) -> None:
        """Called by QTimer for periodic background refresh."""
        self._sync_status = "后台同步中..."
        self.sync_status_changed.emit(self._sync_status)
        try:
            results = self._fetch_service.fetch_all_active()
            total_new = sum(results.values())
            if total_new > 0:
                self._sync_status = f"获取 {total_new} 篇新文章"
            else:
                self._sync_status = "就绪"
        except Exception:
            self._sync_status = "就绪"
        finally:
            self.sync_status_changed.emit(self._sync_status)
            self.feed_list_vm.load_feeds()
            self.article_list_vm.load_articles()
            self.article_list_vm.load_unread_count()

    def _schedule_auto_refresh(self) -> None:
        interval_sec = self._settings_service.get("update_interval", "3600")
        try:
            interval_ms = int(interval_sec) * 1000
        except ValueError:
            interval_ms = 3600000
        self._refresh_timer.start(interval_ms)
