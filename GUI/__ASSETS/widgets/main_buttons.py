# GUI/__ASSETS/widgets/main_buttons.py
from PySide6.QtCore import Qt, QThread, Signal, QObject, QSize
from PySide6.QtGui import QIcon, QPixmap, QPalette, QBrush, QAction
from PySide6.QtWidgets import QToolButton


class CustomMainButton(QToolButton):
    def __init__(self, text, icon_path, width=200, height=200, gradient=("green", "darkgreen")):
        super().__init__()
        self.setText(text)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setFixedSize(width, height)
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(95, 95))
        self.setStyleSheet(f"""
            QToolButton {{
                border-radius: 20px;
                color: white;
                font-size: 25px;
                font-weight: bold;
                border: none;
                padding-top: 20px;  /* décale l’ensemble icône+texte vers le bas */
                padding-bottom: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {gradient[0]}, stop:1 {gradient[1]});
            }}
            QToolButton:hover:!disabled {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {gradient[1]}, stop:1 {gradient[0]});
            }}
            QToolButton:disabled {{
                background: #a0a0a0 !important; 
                color: #d0d0d0 !important;
            }}
        """)
