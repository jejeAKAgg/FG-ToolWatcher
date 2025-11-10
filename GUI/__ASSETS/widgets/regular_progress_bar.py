# GUI/__ASSETS/widgets/regular_progress_bar.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel
from PySide6.QtCore import Qt

class CustomProgressBar(QWidget):
    def __init__(self, height: int = 35, show_text: bool = True, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.process_label = QLabel("")
        self.process_label.setAlignment(Qt.AlignCenter)
        self.process_label.setStyleSheet("font-size: 13pt; color: #333; font-weight: bold;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(height)

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

        self.label = QLabel("0%")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #333;")

        layout.addWidget(self.process_label)
        layout.addWidget(self.progress_bar)
        if show_text:
            layout.addWidget(self.label)
        
    def value(self) -> int:
        
        """
        Return the current value of the bar.
        """
        
        return self.progress_bar.value()

    def set_value(self, value: int):
        
        """
        Update the bar value and the text
        """
        
        self.progress_bar.setValue(value)
        self.label.setText(f"{value}%")

    def set_text(self, text: str):
        
        """
        Update the bar text status.
        """
        
        self.process_label.setText(text)

    def reset(self):
        
        """
        Reset the bar.
        """
        
        self.progress_bar.setValue(0)
        self.label.setText("0%")