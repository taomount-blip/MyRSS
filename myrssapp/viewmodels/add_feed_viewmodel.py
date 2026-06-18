"""Add/Edit Feed ViewModel."""

from PySide6.QtCore import QObject, Signal, Property, QUrl

from ..services.feed_service import FeedService
from ..services.fetch_service import FetchService
from ..models.feed import Feed
from ..models.category import Category
from .base_viewmodel import BaseViewModel


class AddFeedViewModel(BaseViewModel):
    """ViewModel for the Add Feed dialog."""

    feed_preview_ready = Signal(str, str)  # title, description
    feed_added = Signal(Feed)

    def __init__(
        self,
        feed_service: FeedService,
        fetch_service: FetchService,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._feed_service = feed_service
        self._fetch_service = fetch_service
        self._feed_url = ""
        self._categories: list[Category] = []
        self._selected_category_id: int | None = None

    # -- Properties --
    def _get_feed_url(self) -> str:
        return self._feed_url

    def _set_feed_url(self, value: str) -> None:
        self._feed_url = value

    feed_url = Property(str, _get_feed_url, _set_feed_url)

    # -- Actions --
    def load_categories(self) -> None:
        self._categories = self._feed_service.get_all_categories()

    def preview_feed(self) -> None:
        """Fetch feed metadata to show a preview before adding."""
        if not self._feed_url.strip():
            self._emit_error("请输入 RSS 订阅地址")
            return

        self._set_busy(True)
        try:
            parsed = self._fetch_service.fetch_feed_only(self._feed_url.strip())
            if parsed:
                self.feed_preview_ready.emit(parsed.title, parsed.description)
            else:
                self._emit_error("无法获取该订阅源，请检查 URL 是否正确")
        except Exception as e:
            self._emit_error(f"预览失败: {e}")
        finally:
            self._set_busy(False)

    def confirm_add(self) -> Feed | None:
        """Add the feed and return the created Feed object."""
        url = self._feed_url.strip()
        if not url:
            self._emit_error("请输入 RSS 订阅地址")
            return None

        # Validate URL
        qurl = QUrl(url)
        if not qurl.isValid() or not qurl.scheme():
            self._emit_error("URL 格式不正确")
            return None

        # Check duplicate
        existing = self._feed_service.get_feed_by_url(url)
        if existing:
            self._emit_error("该订阅源已存在")
            return None

        self._set_busy(True)
        try:
            from ..services.fetch_service import FetchService
            fetcher = FetchService(self._feed_service._db)

            feed = self._feed_service.add_feed(url, self._selected_category_id)
            article_count = fetcher.fetch_feed(feed)

            feed = self._feed_service.get_feed(feed.id)
            self.feed_added.emit(feed)
            return feed
        except Exception as e:
            self._emit_error(f"添加失败: {e}")
            return None
        finally:
            self._set_busy(False)
