"""Custom delegate rendering for feed tree items."""

from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QIcon
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PySide6.QtCore import QModelIndex


class FeedTreeDelegate(QStyledItemDelegate):
    """Custom tree item delegate for feed list with unread count badge."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon_size = 20

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()

        # Selection highlight
        if option.state & QStyleOptionViewItem.State_Selected:
            painter.fillRect(option.rect, QColor("#e8f0fe"))
        elif option.state & QStyleOptionViewItem.State_MouseOver:
            painter.fillRect(option.rect, QColor("#f5f5f5"))

        # Fetch data
        title = index.data(Qt.DisplayRole)
        unread = index.data(Qt.UserRole) or 0
        is_category = index.data(Qt.UserRole + 1) or False

        if not title:
            painter.restore()
            return

        x = option.rect.x() + 8
        y = option.rect.center().y()

        if is_category:
            # Category: bold text
            font = QFont(painter.font())
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            painter.setFont(font)
            painter.setPen(QColor("#333333"))
            painter.drawText(x, y + 5, str(title))

            painter.restore()
            return

        # Normal feed item
        painter.setPen(QColor("#444444"))
        title_rect = QRect(x, option.rect.y() + 4, option.rect.width() - x - 60, option.rect.height() - 8)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, str(title))

        # Unread badge
        if unread > 0:
            badge_text = str(unread) if unread < 100 else "99+"
            badge_rect = QRect(
                option.rect.right() - 40,
                option.rect.y() + 5,
                30,
                20,
            )
            painter.setBrush(QColor("#1a73e8"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(badge_rect, 10, 10)
            painter.setPen(QColor("#ffffff"))
            font = QFont(painter.font())
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(badge_rect, Qt.AlignCenter, badge_text)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), 32)
