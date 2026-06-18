"""Custom delegate rendering for article list items."""

from PySide6.QtCore import Qt, QSize, QRect, QModelIndex
from PySide6.QtGui import QPainter, QColor, QFont, QTextDocument
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem


class ArticleListDelegate(QStyledItemDelegate):
    """Custom list item delegate for article list display."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()

        # Selection / hover background
        if option.state & QStyleOptionViewItem.State_Selected:
            painter.fillRect(option.rect, QColor("#e8f0fe"))
        elif option.state & QStyleOptionViewItem.State_MouseOver:
            painter.fillRect(option.rect, QColor("#f5f5f5"))

        # Fetch data
        title = index.data(Qt.DisplayRole) or "(无标题)"
        author = index.data(Qt.UserRole) or ""
        published = index.data(Qt.UserRole + 1) or ""
        is_read = index.data(Qt.UserRole + 2) or False
        is_favorited = index.data(Qt.UserRole + 3) or False

        rect = option.rect.adjusted(12, 6, -12, -6)

        # Unread indicator dot
        if not is_read:
            painter.setBrush(QColor("#1a73e8"))
            painter.setPen(Qt.NoPen)
            dot_rect = QRect(rect.x(), rect.y() + 5, 8, 8)
            painter.drawEllipse(dot_rect)

        text_x = rect.x() + (0 if is_read else 16)

        # Title
        title_font = painter.font()
        if not is_read:
            title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#1a1a1a") if not is_read else QColor("#888888"))
        title_rect = QRect(text_x, rect.y(), rect.width() - text_x + 12, 22)
        painter.drawText(title_rect, Qt.AlignLeft, title)

        # Meta line
        meta_y = rect.y() + 24
        meta_parts = []
        if author:
            meta_parts.append(str(author))
        if published:
            meta_parts.append(str(published))

        meta_text = " · ".join(meta_parts)
        meta_font = QFont(painter.font())
        meta_font.setPointSize(9)
        painter.setFont(meta_font)
        painter.setPen(QColor("#999999"))
        meta_rect = QRect(text_x, meta_y, rect.width() - text_x + 12, 18)
        painter.drawText(meta_rect, Qt.AlignLeft, meta_text)

        # Favorite star
        if is_favorited:
            painter.setPen(QColor("#f5a623"))
            star_rect = QRect(rect.right() - 20, rect.y(), 20, 20)
            painter.drawText(star_rect, Qt.AlignCenter, "★")

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), 52)
