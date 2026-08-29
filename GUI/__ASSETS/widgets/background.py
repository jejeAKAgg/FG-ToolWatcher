# GUI/__assets/widgets/background.py
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import QWidget


class BackgroundOverlay(QWidget):

    """
    A widget that displays a background image covered by a semi-transparent color overlay.
    Optimized to rescale the image only when the widget size changes to prevent UI lag.
    """

    def __init__(self, background_path: str | None = None, overlay_color: QColor = QColor(255, 255, 255, 180), parent: QWidget | None = None):

        """
        Initializes the background overlay widget.

        Args:
            bg_path (str, optional): The absolute or relative path to the background image.
            overlay_color (QColor, optional): The color of the overlay with an alpha channel.
                                              Defaults to a semi-transparent white (180 alpha).
            parent (QWidget, optional): The parent widget.
        """
        super().__init__(parent)

        self.overlay_color = overlay_color
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._original_pixmap = QPixmap(background_path) if background_path and os.path.exists(background_path) else None

        self._cached_scaled_pixmap = None

    def resizeEvent(self, event: QResizeEvent):
        """
        Triggered when the widget is resized. Recalculates the scaled image cache.
        """
        super().resizeEvent(event)

        # Only resizing the image when widget size changes
        if self._original_pixmap and not self._original_pixmap.isNull():
            self._cached_scaled_pixmap = self._original_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )

    def paintEvent(self, event: QPaintEvent):
        """
        Paints the cached background image and applies the color overlay.
        """
        painter = QPainter(self)

        # Using cache system in cache instead of re-computation (for optimization purposes)
        if self._cached_scaled_pixmap:
            painter.drawPixmap(0, 0, self._cached_scaled_pixmap)

        # Applying filter
        painter.fillRect(self.rect(), self.overlay_color)
