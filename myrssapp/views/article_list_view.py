"""Article list view – QListView for article headlines."""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListView, QLabel,
    QPushButton, QStyledItemDelegate,
)
from PySide6.QtCore import QAbstractListModel, QModelIndex

from ..viewmodels.article_list_viewmodel import ArticleListViewModel
from ..models.article import Article


class ArticleListModel(QAbstractListModel):
    """Qt model adapter for Article list."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._articles: list[Article] = []

    def set_articles(self, articles: list[Article]) -> None:
        self.beginResetModel()
        self._articles = articles
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._articles)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        article = self._articles[index.row()]

        if role == Qt.DisplayRole:
            return article.title
        if role == Qt.ToolTipRole:
            return article.summary or article.title
        if role == Qt.UserRole:
            return article
        if role == Qt.UserRole + 1:
            return article.is_read
        if role == Qt.UserRole + 2:
            return article.is_favorited
        return None

    def get_article(self, row: int) -> Article | None:
        if 0 <= row < len(self._articles):
            return self._articles[row]
        return None


class ArticleListView(QWidget):
    """Article list panel with filter controls and list view."""

    def __init__(self, viewmodel: ArticleListViewModel, parent=None):
        super().__init__(parent)
        self._vm = viewmodel
        self._model = ArticleListModel()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Filter header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        self._title_label = QLabel("文章")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self._title_label.setFont(font)
        header_layout.addWidget(self._title_label)

        header_layout.addStretch()

        self._unread_btn = QPushButton("未读")
        self._unread_btn.setCheckable(True)
        self._unread_btn.setMaximumWidth(60)
        self._unread_btn.clicked.connect(
            lambda checked: self._vm.set_read_filter(checked)
        )
        header_layout.addWidget(self._unread_btn)

        self._fav_btn = QPushButton("收藏")
        self._fav_btn.setCheckable(True)
        self._fav_btn.setMaximumWidth(60)
        self._fav_btn.clicked.connect(
            lambda checked: self._vm.set_favorite_filter(checked)
        )
        header_layout.addWidget(self._fav_btn)

        layout.addWidget(header)

        # List view
        self._list_view = QListView()
        self._list_view.setModel(self._model)
        self._list_view.setEditTriggers(QListView.NoEditTriggers)
        self._list_view.setSelectionMode(QListView.ExtendedSelection)
        self._list_view.setItemDelegate(ArticleDelegate(self))
        self._list_view.clicked.connect(self._on_clicked)
        layout.addWidget(self._list_view)

        # Pagination bar
        page_bar = QWidget()
        page_layout = QHBoxLayout(page_bar)
        page_layout.setContentsMargins(8, 2, 8, 2)

        self._prev_btn = QPushButton("上一页")
        self._prev_btn.setMaximumWidth(80)
        self._prev_btn.clicked.connect(self._vm.prev_page)
        page_layout.addWidget(self._prev_btn)

        page_layout.addStretch()

        self._mark_all_btn = QPushButton("全部已读")
        self._mark_all_btn.clicked.connect(self._vm.mark_all_read)
        page_layout.addWidget(self._mark_all_btn)

        self._next_btn = QPushButton("下一页")
        self._next_btn.setMaximumWidth(80)
        self._next_btn.clicked.connect(self._vm.next_page)
        page_layout.addWidget(self._next_btn)

        layout.addWidget(page_bar)

        # Data binding
        self._vm.articles_changed.connect(self._on_articles_changed)

    def _on_articles_changed(self) -> None:
        self._model.set_articles(self._vm.articles)

    def _on_clicked(self, index: QModelIndex) -> None:
        article = self._model.get_article(index.row())
        if article:
            self._vm.select_article(article)


class ArticleDelegate(QStyledItemDelegate):
    """Custom rendering for article list items."""

    def sizeHint(self, option, index) -> QSize:
        return QSize(200, 60)

    def paint(self, painter, option, index) -> None:
        painter.save()

        # Background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif index.row() % 2 == 0:
            painter.fillRect(option.rect, option.palette.alternateBase())

        is_read = index.data(Qt.UserRole + 1)
        is_fav = index.data(Qt.UserRole + 2)

        rect = option.rect.adjusted(8, 4, -8, -4)

        # Unread indicator
        if not is_read:
            painter.setBrush(Qt.blue)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect.left(), rect.top() + 6, 8, 8)

        # Title
        title_font = QFont("Microsoft YaHei", 11)
        if not is_read:
            title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(option.palette.text().color())
        title_rect = rect.adjusted(16, 0, -20, -20)
        title = index.data(Qt.DisplayRole) or "(无标题)"
        elided = painter.fontMetrics().elidedText(title, Qt.ElideRight, title_rect.width())
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignTop, elided)

        # Summary (below title)
        summary = index.data(Qt.ToolTipRole) or ""
        if summary:
            summary_font = QFont("Microsoft YaHei", 9)
            painter.setFont(summary_font)
            painter.setPen(Qt.gray)
            summary_rect = rect.adjusted(16, 22, -20, 0)
            elided_summary = painter.fontMetrics().elidedText(
                summary, Qt.ElideRight, summary_rect.width()
            )
            painter.drawText(summary_rect, Qt.AlignLeft | Qt.AlignTop, elided_summary)

        # Favorite star
        if is_fav:
            painter.setPen(Qt.darkYellow)
            painter.drawText(rect.adjusted(rect.width() - 20, 0, 0, 20),
                             Qt.AlignRight | Qt.AlignTop, "★")

        painter.restore()

# QStyle import for the delegate
from PySide6.QtWidgets import QStyle
