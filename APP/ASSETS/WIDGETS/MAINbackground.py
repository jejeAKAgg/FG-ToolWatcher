# APP/widgets/BackgroundOverlay.py
import os

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QColor
from PySide6.QtCore import Qt


class BackgroundOverlay(QWidget):
    def __init__(self, bg_path=None, overlay_color=QColor(255,255,255,180), parent=None):
        super().__init__(parent)
        self.bg_pixmap = QPixmap(bg_path) if bg_path and os.path.exists(bg_path) else None
        self.overlay_color = overlay_color
        self.setAttribute(Qt.WA_StyledBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.bg_pixmap:
            scaled = self.bg_pixmap.scaled(
                self.size(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled)
        painter.fillRect(self.rect(), self.overlay_color)