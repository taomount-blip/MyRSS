"""Loading indicator widget with rotating animation."""

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget


class LoadingIndicator(QWidget):
    """Animated loading spinner."""

    def __init__(self, parent=None, size: int = 24):
        super().__init__(parent)
        self._angle = 0
        self._size = size
        self.setFixedSize(size + 8, size + 8)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._is_spinning = False

    def start(self) -> None:
        self._is_spinning = True
        self._timer.start(50)
        self.show()

    def stop(self) -> None:
        self._is_spinning = False
        self._timer.stop()
        self.hide()

    def _rotate(self) -> None:
        self._angle = (self._angle + 36) % 360
        self.update()

    def paintEvent(self, event) -> None:
        if not self._is_spinning:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = self._size / 2

        pen = QPen(QColor("#1a73e8"), 2.5)
        painter.setPen(pen)

        for i in range(10):
            painter.save()
            painter.translate(center_x, center_y)
            painter.rotate(self._angle + i * 36)
            alpha = int(255 * (i + 1) / 10)
            painter.setPen(QPen(QColor(26, 115, 232, alpha), 2.5))
            painter.drawArc(
                QRectF(-radius / 3, -radius + 2, radius * 2 / 3, radius * 2 / 3),
                0, 60 * 16,
            )
            painter.restore()

        painter.end()
