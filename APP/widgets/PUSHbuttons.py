# widgets/push_buttons.py
from PySide6.QtCore import Qt, QThread, Signal, QObject, QSize
from PySide6.QtGui import QIcon, QPixmap, QPalette, QBrush, QAction
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QTextEdit, QHBoxLayout, QMessageBox, QSizePolicy,
    QToolButton, QMenuBar, QMenu, QCheckBox
)

class CustomPushButton(QPushButton):
    def __init__(self, icon_path, width=100, height=45, bg_color="#82714E", hover_color="#7A6F58", text_color="white", parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(35, 35))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                font-weight: bold;
                border-radius: 20px;
                border: none;
            }}
            QPushButton:hover:!disabled {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background: #a0a0a0; 
                color: #d0d0d0;
            }}
        """)