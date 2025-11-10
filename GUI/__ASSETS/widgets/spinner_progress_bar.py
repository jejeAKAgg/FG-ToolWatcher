# GUI/__ASSETS/widgets/spinner_progress_bar.py
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget


class Spinner(QWidget):
    def __init__(self, parent=None, radius=40, dot_size=10, speed=100, color=(0, 126, 45)):
        """
        :param radius: Rayon du cercle imaginaire
        :param dot_size: Taille des petits ronds
        :param speed: Vitesse de rotation (ms)
        :param color: Couleur RGB (ex: (220, 20, 60) = rouge cramoisi)
        """
        super().__init__(parent)
        self.radius = radius
        self.dot_size = dot_size
        self.angle = 0
        self.color = QColor(*color)

        # Timer pour l’animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(speed)

        size = (radius + dot_size) * 2
        self.setFixedSize(size, size)

    def rotate(self):
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)

        for i in range(12):
            alpha = int(255 * (i + 1) / 12)
            color = QColor(self.color)
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)

            painter.drawEllipse(self.radius, -self.dot_size / 2, self.dot_size, self.dot_size)
            painter.rotate(30)
