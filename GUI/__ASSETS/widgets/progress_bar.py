# GUI/__assets/widgets/progress_bar.py

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class BaseProgressWidget(QWidget):

    """
    Base class for all progress indicator widgets.
    Provides a unified interface to update values, text, and animation states.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

    def set_value(self, value: int):
        """Updates the progress value (typically 0-100)."""
        pass

    def set_text(self, text: str):
        """Updates the descriptive status text."""
        pass

    def reset(self):
        """Resets the indicator to its initial state."""
        pass

    def start(self):
        """Starts the indicator animation (useful for indeterminate spinners)."""
        pass

    def stop(self):
        """Stops the indicator animation."""
        pass


# === CUSTOM PROGRESS BAR(S) ===
# --- LINEAR PROGRESS BAR ---
class LinearProgressBar(BaseProgressWidget):

    """
    A classic linear progress bar with optional percentage and status text.
    """

    def __init__(self, height: int = 35, show_text: bool = True, parent: QWidget | None = None):
        super().__init__(parent)
        self.show_text = show_text

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.process_label = QLabel("")
        self.process_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.process_label.setStyleSheet("font-size: 13pt; color: #333; font-weight: bold;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(height)

        # Apply CSS styling directly to the bar
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #aaa;
                border-radius: 8px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                border-radius: 6px;
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #50C878, stop:1 #3CB371
                );
            }
        """)

        self.percentage_label = QLabel("0%")
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.percentage_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #333;")

        layout.addWidget(self.process_label)
        layout.addWidget(self.progress_bar)

        if self.show_text:
            layout.addWidget(self.percentage_label)

    def value(self) -> int:
        """Returns the current value of the progress bar."""
        return self.progress_bar.value()

    def set_value(self, value: int):
        """Updates the bar value and the percentage text."""
        self.progress_bar.setValue(value)
        if self.show_text:
            self.percentage_label.setText(f"{value}%")

    def set_text(self, text: str):
        """Updates the status text label above the bar."""
        self.process_label.setText(text)

    def reset(self):
        """Resets the bar to 0%."""
        self.progress_bar.setValue(0)
        if self.show_text:
            self.percentage_label.setText("0%")

# --- SPINNER PROGRESS BAR ---
class SpinnerProgressBar(BaseProgressWidget):

    """
    An indeterminate circular spinning progress indicator.
    """

    def __init__(self, radius: int = 40, dot_size: int = 10, speed: int = 100, color: tuple[int, int, int] = (0, 126, 45), parent: QWidget | None = None):

        """
        Args:
            radius (int): Radius of the imaginary circle.
            dot_size (int): Size of the individual dots.
            speed (int): Rotation speed interval in milliseconds.
            color (tuple): RGB color code.
        """
        super().__init__(parent)

        self.radius = radius
        self.dot_size = dot_size
        self.angle = 0
        self.color = QColor(*color)
        self.speed = speed

        # Timer for the animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)

        # We start the timer by default to match the original behavior
        self.start()

        size = (radius + dot_size) * 2
        self.setFixedSize(size, size)

    def _rotate(self):
        """Internal method to update the rotation angle and trigger a repaint."""
        self.angle = (self.angle + 30) % 360
        self.update()

    def start(self):
        """Starts the spinning animation."""
        if not self.timer.isActive():
            self.timer.start(self.speed)

    def stop(self):
        """Stops the spinning animation."""
        if self.timer.isActive():
            self.timer.stop()

    def reset(self):
        """Resets the spinner angle back to top."""
        self.angle = 0
        self.update()

    def paintEvent(self, event):
        """Handles the dynamic drawing of the spinning dots."""
        painter = QPainter(self)
        # Use proper PySide6 Enums for antialiasing and pens
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)

        for i in range(12):
            alpha = int(255 * (i + 1) / 12)
            dot_color = QColor(self.color)
            dot_color.setAlpha(alpha)

            painter.setBrush(dot_color)
            painter.setPen(Qt.PenStyle.NoPen)

            painter.drawEllipse(self.radius, -self.dot_size / 2.0, float(self.dot_size), float(self.dot_size))
            painter.rotate(30)
