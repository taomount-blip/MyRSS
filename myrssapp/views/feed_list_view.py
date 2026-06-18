"""Feed sidebar – QTreeView displaying categories and feeds."""

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtWidgets import QTreeView, QMenu, QInputDialog, QMessageBox

from ..viewmodels.feed_list_viewmodel import FeedListViewModel
from ..models.feed import Feed
from ..models.category import Category


class FeedListView(QTreeView):
    """Tree view showing categories (folders) and feeds (leaf items)."""

    def __init__(self, viewmodel: FeedListViewModel, parent=None):
        super().__init__(parent)
        self._vm = viewmodel
        self._model = QStandardItemModel()
        self.setModel(self._model)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setAnimated(True)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        # "全部文章" root item
        self._all_item = QStandardItem("全部文章")
        self._all_item.setData("all", Qt.UserRole)
        self._all_item.setData(None, Qt.UserRole + 1)
        self._model.appendRow(self._all_item)

        # "收藏" item
        self._fav_item = QStandardItem("收藏")
        self._fav_item.setData("favorites", Qt.UserRole)
        self._fav_item.setData(None, Qt.UserRole + 1)
        self._model.appendRow(self._fav_item)

        # Separator
        sep = QStandardItem("")
        sep.setSelectable(False)
        sep.setEnabled(False)
        self._model.appendRow(sep)

        self.clicked.connect(self._on_clicked)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self._vm.feeds_changed.connect(self._rebuild_tree)

    def _rebuild_tree(self) -> None:
        """Rebuild the tree from the ViewModel data."""
        # Remove category/feed items (keep first 3 special items)
        while self._model.rowCount() > 3:
            self._model.removeRow(3)

        # Add categories with their feeds
        for cat in self._vm.categories:
            cat_item = QStandardItem(cat.name)
            cat_item.setData("category", Qt.UserRole)
            cat_item.setData(cat.id, Qt.UserRole + 1)
            cat_item.setEditable(False)

            feeds = self._vm.get_feeds_for_category(cat.id)
            for feed in feeds:
                feed_item = self._create_feed_item(feed)
                cat_item.appendRow(feed_item)

            self._model.appendRow(cat_item)

        # Uncategorized feeds
        uncategorized = self._vm.get_uncategorized_feeds()
        if uncategorized:
            uncat_parent = QStandardItem("未分类")
            uncat_parent.setData("uncategorized", Qt.UserRole)
            uncat_parent.setEditable(False)
            for feed in uncategorized:
                uncat_parent.appendRow(self._create_feed_item(feed))
            self._model.appendRow(uncat_parent)

        self.expandAll()

    def _create_feed_item(self, feed: Feed) -> QStandardItem:
        unread = f"({feed.unread_count}) " if feed.unread_count > 0 else ""
        label = f"{unread}{feed.title}"
        if feed.error_count > 0:
            label = f"[!] {label}"

        item = QStandardItem(label)
        item.setData("feed", Qt.UserRole)
        item.setData(feed.id, Qt.UserRole + 1)
        item.setEditable(False)
        if feed.unread_count > 0:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        return item

    def _on_clicked(self, index: QModelIndex) -> None:
        item = self._model.itemFromIndex(index)
        if not item:
            return
        kind = item.data(Qt.UserRole)
        entity_id = item.data(Qt.UserRole + 1)

        if kind == "all":
            self._vm.select_feed(None)
        elif kind == "favorites":
            from ..viewmodels.article_list_viewmodel import ArticleListViewModel
            # This is handled by the main VM
            self._vm.select_feed(None)
        elif kind == "category":
            self._vm.select_category(Category(id=entity_id, name=item.text()))
        elif kind == "feed":
            feed = self._vm._feed_service.get_feed(entity_id)
            if feed:
                self._vm.select_feed(feed)

    def _on_context_menu(self, pos) -> None:
        index = self.indexAt(pos)
        if not index.isValid():
            # Right-click on empty area: add category or feed
            menu = QMenu(self)
            menu.addAction("添加订阅", self._on_add_feed)
            menu.addAction("添加分类", self._on_add_category)
            menu.exec_(self.viewport().mapToGlobal(pos))
            return

        item = self._model.itemFromIndex(index)
        if not item:
            return
        kind = item.data(Qt.UserRole)
        entity_id = item.data(Qt.UserRole + 1)

        if kind == "feed":
            menu = QMenu(self)
            menu.addAction("刷新", lambda: self._vm.refresh_feed(entity_id))
            menu.addAction("删除", lambda: self._on_delete_feed(entity_id))
            menu.exec_(self.viewport().mapToGlobal(pos))
        elif kind in ("category", "uncategorized"):
            menu = QMenu(self)
            menu.addAction("添加订阅到此分类", self._on_add_feed)
            if kind == "category":
                menu.addAction("删除分类", lambda: self._on_delete_category(entity_id))
            menu.exec_(self.viewport().mapToGlobal(pos))

    def _on_add_feed(self) -> None:
        self._vm.feeds_changed.emit()  # triggers main_window to open add dialog

    def _on_add_category(self) -> None:
        name, ok = QInputDialog.getText(self, "添加分类", "分类名称:")
        if ok and name.strip():
            self._vm._feed_service.add_category(name.strip())
            self._vm.load_feeds()

    def _on_delete_feed(self, feed_id: int) -> None:
        reply = QMessageBox.question(
            self, "确认删除", "确定删除此订阅及其所有文章？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._vm.delete_feed(feed_id)

    def _on_delete_category(self, category_id: int) -> None:
        reply = QMessageBox.question(
            self, "确认删除", "确定删除此分类？（订阅将移至未分类）",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._vm._feed_service.delete_category(category_id)
            self._vm.load_feeds()
